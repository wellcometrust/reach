"""
Operator to run the web scraper on every organisation.
"""
import os
import logging

from urllib.parse import urlparse

from policytool.airflow.hook.wellcome_s3_hook import WellcomeS3Hook
from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults
from elasticsearch import Elasticsearch


from policytool.elastic.import_epmc_metadata import import_into_elasticsearch


class FetchEPMCMetadata(BaseOperator):
    """ Bulk downloads all metadata XML from EPMC, writing results to
    json.gz in S3.
    """

    template_fields = (
        'src_s3_key',
    )

    @apply_defaults
    def __init__(self, src_s3_key, es_host, es_port, max_epmc_metadata=None,
                 aws_conn_id='aws_default', *args, **kwargs):
        """
        Args:
            src_s3_key: S3 URL for the json.gz output file.
            max_epmc_metadata: Maximum number of EPMC pubs. to process.
            aws_conn_id: Aws connection name.
        """

        super().__init__(*args, **kwargs)

        if not src_s3_key.endswith('.json.gz'):
            raise ValueError('src_s3_key must end in .json.gz')

        self.src_s3_key = src_s3_key
        self.es_host = es_host
        self.es_port = es_port
        self.aws_conn_id = aws_conn_id
        self.max_publications = max_epmc_metadata

    def execute(self, context):
        assert self.src_s3_key.startswith('s3://'), (
                "You must provide a valid s3:// link"
            )

        es = Elasticsearch([{'host': self.es_host, 'port': self.es_port}])
        s3 = WellcomeS3Hook()

        print('Getting %s from bucket' % (self.src_s3_key))
        s3_file = s3.get_key(self.src_s3_key)

        import_into_elasticsearch(s3_file, es)
