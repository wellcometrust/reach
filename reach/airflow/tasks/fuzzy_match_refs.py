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
                 es_index, organisation, min_title_length=0):
        self.es = es
        self.es_index = es_index
        self.score_threshold = score_threshold
        self.min_title_length = min_title_length
        self.should_match_threshold = should_match_threshold
        self.organisation = organisation

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
            ref_metadata = reference.get('metadata', {})
            print("#MATCH_REF", matched_reference)
            print("#REF", reference)
            return {
                'reference_id': reference.get('Reference id', None),
                'extracted_title': reference.get('Title', None),
                'similarity': best_score,
                'organisation': self.organisation,

                # Matched reference information
                'match_title': matched_reference.get('doc', {}).get('title', 'Unknown'),
                'match_algo': 'Fuzzy match',
                'match_pub_year': matched_reference.get('doc', {}).get('pubYear', None),
                'match_authors': ", ".join(list(map(map_author, matched_reference.get('doc', {}).get('authors', [])))),
                'match_publication': matched_reference.get('doc', {}).get('journalTitle', 'Unknown'),
                'match_pmcid': matched_reference.get('doc', {}).get('pmcid', None),
                'match_pmid': matched_reference.get('doc', {}).get('pmid', None),
                'match_doi': matched_reference.get('doc', {}).get('doi', None),
                'match_issn': matched_reference.get('doc', {}).get('journalISSN', None),
                'match_source': 'EPMC',

                # Policy information
                'policy_doc_id': ref_metadata.get("file_hash", None),
                'policy_source_url': ref_metadata.get('url', None),
                'policy_title': ref_metadata.get('title', None),
                'policy_source_page': ref_metadata.get('source_page', None),
                'policy_source_page_title': ref_metadata.get('source_page_title', None),
                'policy_pdf_creator': ref_metadata.get('creator', None),
            }

def map_author(author):
    return "%s %s" % (author.get("LastName", "Unknown"), author.get("Initials", "?"),)



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
                 organisation=None,
                 should_match_threshold=SHOULD_MATCH_THRESHOLD,
                 aws_conn_id='aws_default', *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.src_s3_key = src_s3_key
        self.dst_s3_key = dst_s3_key
        self.score_threshold = score_threshold
        self.should_match_threshold = should_match_threshold
        self.es_index = es_index
        self.organisation = organisation

        self.es = reach.elastic.common.connect(es_hosts)
        self.aws_conn_id = aws_conn_id

    @report_exception
    def execute(self, context):
        with safe_import():
            from reach.refparse.refparse import fuzzy_match_reference

        s3 = WellcomeS3Hook(aws_conn_id=self.aws_conn_id)

        fuzzy_matcher = ElasticsearchFuzzyMatcher(
            self.es,
            self.score_threshold,
            self.should_match_threshold,
            self.es_index,
            self.organisation,
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

