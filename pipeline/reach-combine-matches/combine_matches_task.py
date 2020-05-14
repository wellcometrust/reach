#!/usr/bin/env python3
"""
Operator for combining the fuzzy match results of Reach, to be used
in the evaluator task.

_yield_jsonl_from_gzip, _write_json_gz_to_s3 and _read_json_gz_from_s3
are all duplicated in evaluator_task.py
"""

import os
import tempfile
import logging
import json
import gzip
import argparse

from hooks import s3hook
from hooks.sentry import report_exception

logger = logging.getLogger(__name__)

def _yield_jsonl_from_gzip(fileobj):
    """ Yield a list of dicts read from gzipped json(l)
    """
    with gzip.GzipFile(mode='rb', fileobj=fileobj) as f:
        for line in f:
            yield json.loads(line)

def _write_json_gz_to_s3(s3, data, key):
    """Write a list of jsons to json.gz on s3
    """
    with tempfile.NamedTemporaryFile(mode='wb') as output_raw_f:
        with gzip.GzipFile(mode='wb', fileobj=output_raw_f) as output_f:
            for item in data:
                output_f.write(json.dumps(item).encode('utf-8'))
                output_f.write(b'\n')

        output_raw_f.flush()
        s3.load_file(
            filename=output_raw_f.name,
            dst_key=key
        )

def _read_json_gz_from_s3(s3, key):
    """Write a list of jsons to json.gz on s3
    """
    try:
        with tempfile.TemporaryFile(mode='rb+') as tf:
            key = s3.get_s3_object(key)
            key.download_fileobj(tf)
            tf.seek(0)

            return list(_yield_jsonl_from_gzip(tf))
    except:
        return []

def _get_fuzzy_matches(s3, src_s3_dir_key, organisations):
    """Get all the reach fuzzy matches from all organisations
    and combine into a json.gz.
    """

    fuzzy_matches = []

    for org in organisations:
        src_s3_key = f"{src_s3_dir_key}/{org}/fuzzymatched-refs-{org}.json.gz"
        fuzzy_matches.extend(list(_read_json_gz_from_s3(s3, src_s3_key)))

    return fuzzy_matches

class CombineReachFuzzyMatchesOperator(object):
    """ Combine all Reach fuzzy matches into a single file
    """

    template_fields = (
        'organisations',
        'src_s3_dir_key',
        'dst_s3_key',
    )

    def __init__(self, organisations, src_s3_dir_key, dst_s3_key,
                *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.organisations = organisations
        self.src_s3_dir_key = src_s3_dir_key
        self.dst_s3_key = dst_s3_key

    @report_exception
    def execute(self):
        s3 = s3hook.S3Hook()

        fuzzy_matches = _get_fuzzy_matches(s3,
            self.src_s3_dir_key, self.organisations)

        logger.info(
            'CombineReachFuzzyMatchesOperator: read %d lines from %s files',
            len(fuzzy_matches),
            len(self.organisations),
            )

        # Write the results to S3

        _write_json_gz_to_s3(s3, fuzzy_matches, key=self.dst_s3_key)

        logger.info(
            'CombineReachFuzzyMatchesOperator: wrote %d lines to %s.',
            len(fuzzy_matches),
            self.dst_s3_key
        )
        logger.info(
            'CombineReachFuzzyMatchesOperator: Done combining reach fuzzy matches.'
        )

if __name__ == '__main__':

    arg_parser = argparse.ArgumentParser(
        description='Combines the fuzzy match results into one list'
                    ' written to the given S3 path.'
    )
    arg_parser.add_argument(
        'src_s3_key',
        help='The source path to s3.'
    )
    arg_parser.add_argument(
        'dst_s3_key',
        help='The destination path to s3.'
    )

    args = arg_parser.parse_args()

    combineReachFuzzyMatchRefs = CombineReachFuzzyMatchesOperator(
        organisations=s3hook.ORGS,
        src_s3_dir_key=args.src_s3_key,
        dst_s3_key=args.dst_s3_key
        )
    combineReachFuzzyMatchRefs.execute()
