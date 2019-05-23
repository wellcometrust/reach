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

from policytool.refparse.refparse import yield_structured_references
from policytool.airflow.hook.wellcome_s3_hook import WellcomeS3Hook


logger = logging.getLogger(__name__)

RESOURCE_FILES = '/src/policytool/resources/'


class ExtractRefsOperator(BaseOperator):
    """
    Reads reference sections from a single newline-delimited
    json.gz file, writing out parsed references as a single
    newline-delimited json.gz file.

    Args:
        src_s3_key:
        dst_s3_key: S3 location for output
    """

    @apply_defaults
    def __init__(self, model_path, src_s3_key, dst_s3_key, aws_conn_id='aws_default', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model_path = model_path
        self.src_s3_key = src_s3_key
        self.dst_s3_key = dst_s3_key
        self.aws_conn_id = aws_conn_id

    def execute(self, context):

        model_path = 's3://{path}'.format(
            path=self.model_path,
        )
        src_s3_key = 's3://{path}'.format(
            path=self.src_s3_key,
        )
        dst_s3_key = 's3://{path}'.format(
            path=self.dst_s3_key,
        )
        
        pool_map = map

        s3 = WellcomeS3Hook(aws_conn_id=self.aws_conn_id)

        with tempfile.NamedTemporaryFile() as dst_rawf:
            with gzip.GzipFile(mode='wb', fileobj=dst_rawf) as dst_f:
                refs = yield_structured_references(
                    src_s3_key,
                    model_path,
                    pool_map,
                    logger)
                for doc_id, structured_references in refs:
                    for row in structured_references.iterrows():
                        print(row)
                        d = {'docId': doc_id}
                        for (col_name, value) in enumerate(row):
                            d.update({col_name : value})
                        print(d)
                        # TODO: update d with attrs from row (d.update()?)
                        dst_f.write(json.dumps(d).encode('utf-8'))
                        dst_f.write(b'\n')

            dst_rawf.flush()

            s3.load_file(
                filename=dst_rawf.name,
                key=dst_s3_key,
                replace=True,
            )


