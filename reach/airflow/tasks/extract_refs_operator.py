"""
Operator to run the web scraper on every organisation.
"""
import os
import logging
import tempfile
import json
import gzip

from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults

from reach.airflow.hook.wellcome_s3_hook import WellcomeS3Hook
from reach.airflow.safe_import import safe_import
from reach.sentry import report_exception


logger = logging.getLogger(__name__)


class ExtractRefsOperator(BaseOperator):
    """
    Reads reference sections from a single newline-delimited
    json.gz file, writing out parsed references as a single
    newline-delimited json.gz file.

    Args:
        src_s3_key: S3 URL for input
        split_s3_key: S3 URL for split references
        parsed_s3_key: S3 URL for parsed references
    """

    template_fields = (
        'src_s3_key',
        'split_s3_key',
        'parsed_s3_key',
    )

    @apply_defaults
    def __init__(self, src_s3_key, split_s3_key, parsed_s3_key,
                 aws_conn_id='aws_default', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.src_s3_key = src_s3_key
        self.split_s3_key = split_s3_key
        self.parsed_s3_key = parsed_s3_key
        self.aws_conn_id = aws_conn_id

    @report_exception
    def execute(self, context):
        with safe_import():
            from reach.refparse.refparse import yield_structured_references

        pool_map = map
        s3 = WellcomeS3Hook(aws_conn_id=self.aws_conn_id)

        with tempfile.NamedTemporaryFile() as split_rawf, tempfile.NamedTemporaryFile() as parsed_rawf:
            with gzip.GzipFile(mode='wb', fileobj=split_rawf) as split_f, gzip.GzipFile(mode='wb', fileobj=parsed_rawf) as parsed_f:
                split_refs, parsed_refs = yield_structured_references(
                    self.src_s3_key,
                    pool_map,
                    logger)
                for structured_references in split_refs:
                    for ref in structured_references:
                        split_f.write(json.dumps(ref).encode('utf-8'))
                        split_f.write(b'\n')
                for parsed_references in parsed_refs:
                    for ref in parsed_references:
                        parsed_f.write(json.dumps(ref).encode('utf-8'))
                        parsed_f.write(b'\n')

            split_rawf.flush()
            parsed_rawf.flush()

            s3.load_file(
                filename=split_rawf.name,
                key=self.split_s3_key,
                replace=True,
            )

            s3.load_file(
                filename=parsed_rawf.name,
                key=self.parsed_s3_key,
                replace=True,
            )

