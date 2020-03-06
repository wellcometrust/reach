#!/usr/bin/env python3
"""
Operator to run the web scraper on every organisation.
"""
import logging
import tempfile
import json
import gzip

from hooks.s3hook import S3Hook
from hooks.sentry import report_exception
from safe_import import safe_import


logging.baseConfig()
logger = logging.getLogger(__name__)


class ExtractRefsOperator(object):
    """
    Reads reference sections from a single newline-delimited
    json.gz file, writing out parsed references as a single
    newline-delimited json.gz file.

    Args:
        src_s3_key: S3 URL for input
        split_s3_key: S3 URL for split references
        parsed_s3_key: S3 URL for parsed references
    """

    def __init__(self, src_s3_key, split_s3_key, parsed_s3_key,
                 aws_conn_id='aws_default'):
        self.src_s3_key = src_s3_key
        self.split_s3_key = split_s3_key
        self.parsed_s3_key = parsed_s3_key
        self.aws_conn_id = aws_conn_id

    @report_exception
    def execute(self, context):
        with safe_import():
            from refparse.refparse import yield_structured_references

        pool_map = map
        s3 = S3Hook()

        with tempfile.NamedTemporaryFile() as split_rawf, \
             tempfile.NamedTemporaryFile() as parsed_rawf:

            with gzip.GzipFile(mode='wb', fileobj=split_rawf) as split_f, \
                 gzip.GzipFile(mode='wb', fileobj=parsed_rawf) as parsed_f:

                refs = yield_structured_references(
                    self.src_s3_key,
                    pool_map,
                    logger)
                for split_references, parsed_references in refs:
                    split_f.write(json.dumps(split_references).encode('utf-8'))
                    split_f.write(b'\n')
                    for ref in parsed_references:
                        parsed_f.write(json.dumps(ref).encode('utf-8'))
                        parsed_f.write(b'\n')

            split_rawf.flush()
            parsed_rawf.flush()

            s3.client.load_file(
                filename=split_rawf.name,
                key=self.split_s3_key,
                replace=True,
            )

            s3.client.load_file(
                filename=parsed_rawf.name,
                key=self.parsed_s3_key,
                replace=True,
            )
