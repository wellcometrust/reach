"""
Operators for fetching data from dimensions.ai.
"""

import logging
from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults


logger = logging.getLogger(__name__)


class TestTaskOperator(BaseOperator):
    """
    Pulls data from the dimensions.ai to a bucket in S3.

    Args:
        data_source: 'grants' or 'publications'
        year: year for which to pull data (int)
        s3_key: destination url (s3://BUCKET_NAME/KEY_NAME)
        aws_conn_id: AWS connection name
        dimensions_conn_id: dimensions.ai connection name
        replace: True if task should overwrite existing s3 key
    """

    @apply_defaults
    def __init__(self, *args, **kwargs):
        super(TestTaskOperator, self).__init__(*args, **kwargs)

    def execute(self, context):
        # Allow overriding replace when running with
        # `airflow test ... -tp '{"replace": true}'
        # (this may belong elsewhere)
        print('Hello World')
