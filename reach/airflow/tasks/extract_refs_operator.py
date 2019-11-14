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
        dst_s3_key: S3 URL for output
    """

    template_fields = (
        'src_s3_key',
        'dst_s3_key',
    )

    @apply_defaults
    def __init__(self, src_s3_key, dst_s3_key, aws_conn_id='aws_default', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.src_s3_key = src_s3_key
        self.dst_s3_key = dst_s3_key
        self.aws_conn_id = aws_conn_id

    @report_exception
    def execute(self, context):
        with safe_import():
            from reach.refparse.refparse import yield_structured_references

        pool_map = map
        s3 = WellcomeS3Hook(aws_conn_id=self.aws_conn_id)

        with tempfile.NamedTemporaryFile() as dst_rawf:
            with gzip.GzipFile(mode='wb', fileobj=dst_rawf) as dst_f:
                refs = yield_structured_references(
                    self.src_s3_key,
                    pool_map,
                    logger)
                for structured_references in refs:
                    for ref in structured_references:
                        dst_f.write(json.dumps(ref).encode('utf-8'))
                        dst_f.write(b'\n')

            dst_rawf.flush()

            s3.load_file(
                filename=dst_rawf.name,
                key=self.dst_s3_key,
                replace=True,
            )


