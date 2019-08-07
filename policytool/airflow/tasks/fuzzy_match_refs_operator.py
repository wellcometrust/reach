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


def yield_structured_references(s3, structured_references_path):
    with tempfile.TemporaryFile(mode='rb+') as tf:
        key = s3.get_key(structured_references_path)
        key.download_fileobj(tf)

        tf.seek(0)

        with gzip.GzipFile(mode='rb', fileobj=tf) as f:
            for line in f:
                yield json.loads(line)

class ElasticsearchFuzzyMatcher:
    def __init__(self, es, score_threshold, should_match_threshold, title_length_threshold=0):
        self.es = es
        self.score_threshold = score_threshold
        self.title_length_threshold = title_length_threshold
        self.should_match_threshold = should_match_threshold

    def match(self, reference):
        title = reference['Title']

        if len(title) < self.title_length_threshold:
            return

        body = {
            "query": {
                "match": {
                    "title": {
                        "query": title,
                        "minimum_should_match": f"{self.should_match_threshold}%"
                    }
                }
            }
        }
        res = self.es.search(
            index="datalabs-references",
            body=body,
            size=1
        )

        matches_count = res['hits']['total']['value']
        if matches_count == 0:
            return
        
        best_match = res['hits']['hits'][0]
        best_score = best_match['_score']
        if best_score > self.score_threshold:
            matched_reference = best_match['_source']
            return {
                'Document id': reference['Document id'],
                'Reference id': reference['Reference id'],
                'Extracted title': reference['Title'],
                'Matched title': matched_reference['title'],
                'Similarity': best_score,
                'Match algorithm': 'Fuzzy match'
            }
  

class FuzzyMatchRefsOperator(BaseOperator):
    """
    Matches references to known publications in the database

    Args:
        references: The references to match against the database
    """

    @apply_defaults
    def __init__(self, es_host, structured_references_path, fuzzy_matched_references_path,
                 score_threshold, should_match_threshold, aws_conn_id='aws_default', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.structured_references_path = structured_references_path
        self.fuzzy_matched_references_path = fuzzy_matched_references_path
        self.score_threshold = score_threshold
        self.should_match_threshold = should_match_threshold
 
        self.es_host = es_host
        self.es = Elasticsearch([self.es_host])
        self.aws_conn_id = aws_conn_id

    @report_exception
    def execute(self, context):
        with safe_import():
            from policytool.refparse.refparse import fuzzy_match_reference

        structured_references_path = 's3://{path}'.format(
            path=self.structured_references_path,
        )
        fuzzy_matched_references_path = 's3://{path}'.format(
            path=self.fuzzy_matched_references_path,
        )
        s3 = WellcomeS3Hook(aws_conn_id=self.aws_conn_id)
    
        fuzzy_matcher = ElasticsearchFuzzyMatcher(
            self.es,
            self.score_threshold,
            self.should_match_threshold
        )

        with tempfile.NamedTemporaryFile(mode='wb') as output_raw_f:
            with gzip.GzipFile(mode='wb', fileobj=output_raw_f) as output_f:
                for structured_reference in yield_structured_references(s3, structured_references_path):
                    fuzzy_matched_reference = fuzzy_match_reference(
                        fuzzy_matcher,
                        structured_reference
                    )
                    if fuzzy_matched_reference:
                        logger.info("Match")
                        
                        output_f.write(json.dumps(fuzzy_matched_reference).encode('utf-8'))
                        output_f.write(b'\n')

            output_raw_f.flush()

            s3.load_file(
                filename=output_raw_f.name,
                key=fuzzy_matched_references_path,
                replace=True,
            )
