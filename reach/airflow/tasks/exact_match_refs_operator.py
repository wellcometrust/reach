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

import reach.elastic.common
from reach.airflow.hook.wellcome_s3_hook import WellcomeS3Hook
from reach.airflow.safe_import import safe_import
from reach.sentry import report_exception

logger = logging.getLogger(__name__)

def yield_publications(s3, epmc_metadata_object):

    with tempfile.TemporaryFile(mode='rb+') as tf:
        key = epmc_metadata_object
        key.download_fileobj(tf)
        tf.seek(0)
        with gzip.GzipFile(mode='rb', fileobj=tf) as f:
            for line in f:
                yield json.loads(line)


class ElasticsearchExactMatcher:

    def __init__(self, es, es_full_text_index, title_length_threshold):
        self.es = es
        self.es_full_text_index = es_full_text_index
        self.title_length_threshold = title_length_threshold

    def match(self, publication):
        
        if 'title' not in publication:
            return

        title = publication['title']

        # Exclude short titles that create noisy matches
        if len(title) < self.title_length_threshold:
            return

        body = {
            "query": {
                "match_phrase": {
                    "doc.text": title
                }
            },
            "_source": ["doc.hash"],

        }
        res = self.es.search(
            index=self.es_full_text_index,
            body=body,
            size=1000 # if there are more than 1000, need to paginate
        )

        for match in res['hits']['hits']:
            pub_doi = publication['doi'] if 'doi' in publication else None
            pub_pmid = publication['pmid'] if 'pmid' in publication else None

            yield {
                'Document id': match['_source']['doc']['hash'],
                'Matched publication doi': pub_doi, 
                'Matched publication pmid': pub_pmid,
                'Matched title': title,
                'Match algorithm': 'Exact match'
            }


class ExactMatchRefsOperator(BaseOperator):
    """
    Matches references to known publications in the database

    Args:
        references: The references to match against the database
    """
    template_fields = (
        'epmc_metadata_key',
        'exact_matched_references_path',
    )

    TITLE_LENGTH_THRESHOLD = 40

    @apply_defaults
    def __init__(self, es_hosts, epmc_metadata_key,
                exact_matched_references_path,
                es_full_text_index,
                title_length_threshold=TITLE_LENGTH_THRESHOLD,
                aws_conn_id='aws_default', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.epmc_metadata_key = epmc_metadata_key
        self.exact_matched_references_path = exact_matched_references_path
        self.es_full_text_index = es_full_text_index
        self.title_length_threshold = title_length_threshold
        self.es_hosts = es_hosts
        self.es = reach.elastic.common.connect(es_hosts)
        self.aws_conn_id = aws_conn_id

    @report_exception
    def execute(self, context):
        with safe_import():
            from reach.refparse.refparse import exact_match_publication

        s3 = WellcomeS3Hook(aws_conn_id=self.aws_conn_id)

        exact_matcher = ElasticsearchExactMatcher(
            self.es,
            self.es_full_text_index,
            self.title_length_threshold
        )

        epmc_metadata_object = s3.get_key(self.epmc_metadata_key)
        
        logger.info(
            'ExactMatchRefsOperator: Getting publications from %s', epmc_metadata_object
        )

        with tempfile.NamedTemporaryFile(mode='wb') as output_raw_f:
            with gzip.GzipFile(mode='wb', fileobj=output_raw_f) as output_f:
                publications = yield_publications(s3, epmc_metadata_object)
                count = 0
                count_match = 0
                for publication in publications:
                    count += 1
                    if count % 100000 == 0:
                        logger.info(
                            'ExactMatchRefsOperator: publications=%d', count
                            )
                    exact_matched_references = exact_match_publication(
                        exact_matcher,
                        publication
                    )
                    for exact_matched_reference in exact_matched_references:
                        if exact_matched_reference:
                            count_match += 1
                            if count_match % 500 == 0:
                                logger.info(
                                    'ExactMatchRefsOperator: matches=%d', count_match
                                    )
                            output_f.write(json.dumps(exact_matched_reference).encode('utf-8'))
                            output_f.write(b'\n')
                            
            output_raw_f.flush()

            s3.load_file(
                filename=output_raw_f.name,
                key=self.exact_matched_references_path,
                replace=True,
            )

            logger.info(
                    'ExactMatchRefsOperator: publications=%d matches=%d',
                    count, count_match
                )
            logger.info(
                    'ExactMatchRefsOperator: Matches saved to %s',
                    s3.get_key(self.exact_matched_references_path)
                )

