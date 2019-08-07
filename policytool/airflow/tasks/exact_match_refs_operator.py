"""
Operator for matching references to publications in database
"""
import tempfile
import logging
import gzip
import json
import os


from elasticsearch import Elasticsearch

from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults

from policytool.airflow.hook.wellcome_s3_hook import WellcomeS3Hook
from policytool.airflow.safe_import import safe_import
from policytool.sentry import report_exception

logger = logging.getLogger(__name__)


def yield_publications(s3, publications_path):
    with tempfile.TemporaryFile(mode='rb+') as tf:
        key = s3.get_key(publications_path)
        key.download_fileobj(tf)

        tf.seek(0)

        with gzip.GzipFile(mode='rb', fileobj=tf) as f:
            for line in f:
                yield json.loads(line)
 
class ElasticsearchExactMatcher:
    def __init__(self, es, title_length_threshold):
        self.es = es
        self.title_length_threshold = title_length_threshold

    def match(self, publication):
        title = publication['title']
        
        # Exclude short titles that create noisy matches
        if len(title) < self.title_length_threshold:
            return

        body = {
            "query": {
                "match_phrase": {
                    "section": title
                }
            },
            "_source": ["hash"],
            
        }
        res = self.es.search(
            index="datalabs-sections",
            body=body,
            size=1000 # if there are more than 1000, need to paginate
        )
        
        for match in res['hits']['hits']:
            score = match['_score']
 
            matched_policy_document = match['_source']
            yield {
                'Document id': matched_policy_document['hash'],
                'Matched publication id': publication['uber_id'],
                'Matched title': title,
                'Match algorithm': 'Exact match'
            }
  

class ExactMatchRefsOperator(BaseOperator):
    """
    Matches references to known publications in the database

    Args:
        references: The references to match against the database
    """

    @apply_defaults
    def __init__(self, es_host, publications_path, exact_matched_references_path,
                 title_length_threshold, aws_conn_id='aws_default', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.publications_path = publications_path
        self.exact_matched_references_path = exact_matched_references_path
        self.title_length_threshold = title_length_threshold
        self.es_host = es_host
        self.es = Elasticsearch([self.es_host])
        self.aws_conn_id = aws_conn_id

    @report_exception
    def execute(self, context):
        with safe_import():
            from policytool.refparse.refparse import exact_match_publication

        publications_path = 's3://{path}'.format(
            path=self.publications_path,
        )
        exact_matched_references_path = 's3://{path}'.format(
            path=self.exact_matched_references_path,
        )

        s3 = WellcomeS3Hook(aws_conn_id=self.aws_conn_id)
    
        exact_matcher = ElasticsearchExactMatcher(
            self.es,
            self.title_length_threshold
        )

        with tempfile.NamedTemporaryFile(mode='wb') as output_raw_f:
            with gzip.GzipFile(mode='wb', fileobj=output_raw_f) as output_f:
                publications = yield_publications(s3, publications_path)
                for publication in publications:
                    exact_matched_references = exact_match_publication(
                        exact_matcher,
                        publication
                    )
                    for exact_matched_reference in exact_matched_references:
                        if exact_matched_reference:
                            logger.info("Match")
                        
                            output_f.write(json.dumps(exact_matched_reference).encode('utf-8'))
                            output_f.write(b'\n')

            output_raw_f.flush()

            s3.load_file(
                filename=output_raw_f.name,
                key=exact_matched_references_path,
                replace=True,
            )
