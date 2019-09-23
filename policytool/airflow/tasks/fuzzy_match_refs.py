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
    MAX_TITLE_LENGTH = 512

    def __init__(self, es, score_threshold, should_match_threshold,
                 es_index, min_title_length=0):
        self.es = es
        self.es_index = es_index
        self.score_threshold = score_threshold
        self.min_title_length = min_title_length
        self.should_match_threshold = should_match_threshold

    def match(self, reference):
        title = reference['Title']
        title_len = len(title)

        if title_len < self.min_title_length:
            return

        if title_len > self.MAX_TITLE_LENGTH:
            # ExtractRefs does not always yield journal titles;
            # sometimes it just yields back a wholesale paragraph
            # of text from somewhere in the document. Truncate this
            # because sending it up to ES results in an error.
            # (We may want to just skip long titles instead...and
            # certainly should monitor them.)
            title = ' '.join(
                title[:self.MAX_TITLE_LENGTH].split()[:-1]
            )
            logger.info(
                'ElasticsearchFuzzyMatcher.match: '
                'orig-length=%d doc-id=%s truncated-title=%r',
                title_len, reference['Document id'], title
            )

        body = {
            "query": {
                "match": {
                    "doc.title": {
                        "query": title,
                        "minimum_should_match": f"{self.should_match_threshold}%"
                    }
                }
            }
        }
        res = self.es.search(
            index=self.es_index,
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
            # logger.info(
            #     'ElasticsearchFuzzyMatcher.match: '
            #     'doc-id=%s similarity=%.1f',
            #     reference['Document id'], best_score
            # )
            return {
                'Document id': reference['Document id'],
                'Reference id': reference['Reference id'],
                'Extracted title': reference['Title'],
                'Matched title': matched_reference['doc']['title'],
                'Similarity': best_score,
                'Match algorithm': 'Fuzzy match'
            }


class FuzzyMatchRefsOperator(BaseOperator):
    """
    Matches references to known publications in the database

    Args:
        references: The references to match against the database
    """

    template_fields = (
        'src_s3_key',
        'dst_s3_key'
    )

    SHOULD_MATCH_THRESHOLD = 80
    SCORE_THRESHOLD = 50

    @apply_defaults
    def __init__(self, es_hosts, src_s3_key, dst_s3_key, es_index,
                 score_threshold=SCORE_THRESHOLD,
                 should_match_threshold=SHOULD_MATCH_THRESHOLD,
                 aws_conn_id='aws_default', *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.src_s3_key = src_s3_key
        self.dst_s3_key = dst_s3_key
        self.score_threshold = score_threshold
        self.should_match_threshold = should_match_threshold
        self.es_index = es_index

        self.es = Elasticsearch(es_hosts)
        self.aws_conn_id = aws_conn_id

    @report_exception
    def execute(self, context):
        with safe_import():
            from policytool.refparse.refparse import fuzzy_match_reference

        s3 = WellcomeS3Hook(aws_conn_id=self.aws_conn_id)

        fuzzy_matcher = ElasticsearchFuzzyMatcher(
            self.es,
            self.score_threshold,
            self.should_match_threshold,
            self.es_index,
        )

        with tempfile.NamedTemporaryFile(mode='wb') as output_raw_f:
            with gzip.GzipFile(mode='wb', fileobj=output_raw_f) as output_f:
                refs = yield_structured_references(s3, self.src_s3_key)
                match_count = 0
                count = 0
                for count, structured_reference in enumerate(refs, 1):
                    if count % 500 == 0:
                        logger.info(
                            'FuzzyMatchRefsOperator: references=%d', count
                        )
                    fuzzy_matched_reference = fuzzy_match_reference(
                        fuzzy_matcher,
                        structured_reference
                    )
                    if fuzzy_matched_reference:
                        match_count += 1
                        if match_count % 100 == 0:
                            logger.info(
                                'FuzzyMatchRefsOperator: matches=%d',
                                match_count
                            )
                        output_f.write(json.dumps(fuzzy_matched_reference).encode('utf-8'))
                        output_f.write(b'\n')

            output_raw_f.flush()
            s3.load_file(
                filename=output_raw_f.name,
                key=self.dst_s3_key,
                replace=True,
            )
            logger.info(
                'FuzzyMatchRefsOperator: references=%d matches=%d',
                count, match_count
            )

