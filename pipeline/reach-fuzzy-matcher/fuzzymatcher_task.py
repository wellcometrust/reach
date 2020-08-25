#!/usr/bin/env python3
"""
Operator for matching references to publications in database
"""
import tempfile
import logging
import gzip
import json
import os
import argparse

import elastic.common
from hooks import s3hook
from hooks.sentry import report_exception

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def yield_structured_references(s3, structured_references_path):
    with tempfile.TemporaryFile(mode='rb+') as tf:
        key = s3.get_s3_object(structured_references_path)
        key.download_fileobj(tf)
        tf.seek(0)
        with gzip.GzipFile(mode='rb', fileobj=tf) as f:
            for line in f:
                yield json.loads(line)


def map_author(author):
    return "%s %s" % (
        author.get(
            "LastName",
            "Unknown"
        ), author.get("Initials", "?"),)


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
        if not reference.get('Title'):
            return

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
                title_len, reference.get('document_id', "Unkown ID"), title
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
            return {
                'reference_id': reference.get('reference_id', None),
                'extracted_title': reference.get('Title', None),
                'similarity': best_score,

                # Matched reference information
                'match_id': best_match.get('_id'),
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
                'associated_policies_count': 1,

                # Policy information
                'policies': [{
                    'doc_id': ref_metadata.get("file_hash", None),
                    'source_url': ref_metadata.get('url', None),
                    'title': ref_metadata.get('title', None),
                    'source_page': ref_metadata.get('source_page', None),
                    'source_page_title': ref_metadata.get('source_page_title', None),
                    'pdf_creator': ref_metadata.get('creator', None),
                    'organisation': self.organisation,
                }]
            }


class FuzzyMatchRefsOperator(object):
    """
    Matches references to known publications in the database

    Args:
        references: The references to match against the database
    """

    template_fields = (
        'src_s3_key',
        'dst_s3_key'
    )

    def __init__(self, es_hosts, src_s3_key, dst_s3_key, es_index,
                 score_threshold=50,
                 organisation=None,
                 should_match_threshold=80):

        self.src_s3_key = src_s3_key
        self.dst_s3_key = dst_s3_key
        self.score_threshold = score_threshold
        self.should_match_threshold = should_match_threshold
        self.es_index = es_index
        self.organisation = organisation

        self.es = elastic.common.connect(es_hosts)

    @report_exception
    def execute(self):
        s3 = s3hook.S3Hook()

        fuzzy_matcher = ElasticsearchFuzzyMatcher(
            self.es,
            self.score_threshold,
            self.should_match_threshold,
            self.es_index,
            self.organisation,
        )
        refs = yield_structured_references(s3, self.src_s3_key)
        match_count = 0
        count = 0
        references = {}
        for count, structured_reference in enumerate(refs, 1):
            if count % 500 == 0:
                logger.info(
                    'FuzzyMatchRefsOperator: references=%d', count
                )
            fuzzy_matched_reference = fuzzy_matcher.match(
                structured_reference
            )
            if fuzzy_matched_reference:
                ref_id = fuzzy_matched_reference['match_id']
                if ref_id in references.keys():

                    references[ref_id][
                        'associated_policies_count'] += 1

                    references[ref_id]['policies'].append(
                        fuzzy_matched_reference['policies'][0]
                    )
                else:
                    references[ref_id] = fuzzy_matched_reference

                match_count += 1
                if match_count % 100 == 0:
                    logger.info(
                        'FuzzyMatchRefsOperator: matches=%d',
                        match_count
                    )

        with tempfile.NamedTemporaryFile(mode='wb') as output_raw_f:
            with gzip.GzipFile(mode='wb', fileobj=output_raw_f) as output_f:
                # This probably looks really odd, but we're basically ensuring that if there are no citations,
                # that we still at least write a blank string to the start of the file so that
                # the pipeline doesn't freak out on openining an empty GZip file
                output_f.write(b' ')
                for reference in references.values():
                    output_f.write(json.dumps(reference).encode('utf-8'))
                    output_f.write(b'\n')

            output_raw_f.flush()
            s3.load_file(
                output_raw_f.name,
                self.dst_s3_key,
            )

            logger.info(
                    'FuzzyMatchRefsOperator: Matches saved to %s',
                    s3.get_s3_object(self.dst_s3_key)
                )


if __name__ == '__main__':
    es_host = os.environ['ES_HOST']
    es_port = os.environ.get('ES_PORT', 9200)

    es_hosts = [(es_host, es_port)]
    arg_parser = argparse.ArgumentParser(
        description='Run a web scraper for a given organisation and writes the'
                    ' results to the given S3 path.'
    )
    arg_parser.add_argument(
        'src_s3_key',
        help='The source path to s3.'
    )
    arg_parser.add_argument(
        'dst_s3_key',
        help='The destination path to s3.'
    )
    arg_parser.add_argument(
        'organisation',
        choices=s3hook.ORGS,
        default=None,
        help='The organisation to match citations with.'
    )
    arg_parser.add_argument(
        'epmc_es_index',
        help='The index where EPMC data is stored.'
    )
    arg_parser.add_argument(
        '--score_threshold',
        default=50,
        help="The maximum number of items to index."
    )
    arg_parser.add_argument(
        '--should_match_threshold',
        default=80,
        help="The maximum number of items to index."
    )

    args = arg_parser.parse_args()

    fuzzy_matcher = FuzzyMatchRefsOperator(
        es_hosts,
        args.src_s3_key,
        args.dst_s3_key,
        args.epmc_es_index,
        score_threshold=args.score_threshold,
        organisation=args.organisation,
        should_match_threshold=args.should_match_threshold
    )
    fuzzy_matcher.execute()
