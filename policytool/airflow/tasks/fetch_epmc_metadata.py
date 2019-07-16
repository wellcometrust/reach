"""
Operator to run the get the latest EPMC metadata from AWS S3.
"""

from policytool.airflow.hook.wellcome_s3_hook import WellcomeS3Hook
from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults
from elasticsearch import Elasticsearch

from policytool.elastic.import_epmc_metadata import (
    import_into_elasticsearch,
    clean_es,
)


class FetchEPMCMetadata(BaseOperator):
    """ Bulk downloads all metadata XML from EPMC, writing results to
    json.gz in S3.
    """

    template_fields = (
        'src_s3_key',
    )

    @apply_defaults
    def __init__(self, src_s3_key, es_host, es_port=9200,
                 max_epmc_metadata=None, aws_conn_id='aws_default',
                 *args, **kwargs):
        """
        Args:
            src_s3_key: S3 URL for the json.gz output file.
            es_host: the hostname of elasticsearch database.
            es_port: the port of elasticsearch database. Default to 9200.
            max_epmc_metadata: Maximum number of EPMC pubs to process.
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

        es = Elasticsearch([{'host': self.es_host, 'port': self.es_port}])
        s3 = WellcomeS3Hook()

        # TODO: implement skipping mechanism
        # clean_es(es)

        self.log.info(
            'Getting %s pubs from %s',
            self.max_publications if self.max_publications else 'all',
            self.src_s3_key,
        )

        s3_file = s3.get_key(self.src_s3_key)

        line_count = import_into_elasticsearch(
            s3_file,
            es,
            self.max_publications
        )

        self.log.info(
            'imported %d lines into elasticsearch',
            line_count['count'],
        )
