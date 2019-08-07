"""
Operator to run the get the latest EPMC metadata from AWS S3.
"""

import tempfile

from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults
from elasticsearch import Elasticsearch

from policytool.airflow.hook.wellcome_s3_hook import WellcomeS3Hook
from policytool.elastic.import_epmc_metadata import import_into_elasticsearch
from policytool.elastic.import_epmc_metadata import clean_es


class ESIndexPublications(BaseOperator):
    """ Download EPMC publication metadatas stored in S3 and index them with
    Elasticsearch.
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
        self.max_epmc_metadata = max_epmc_metadata

    def execute(self, context):

        es = Elasticsearch([{'host': self.es_host, 'port': self.es_port}])
        s3 = WellcomeS3Hook()

        # TODO: implement skipping mechanism
        clean_es(es)

        self.log.info(
            'Getting %s pubs from %s',
            self.max_epmc_metadata if self.max_epmc_metadata else 'all',
            self.src_s3_key,
        )

        s3_object = s3.get_key(self.src_s3_key)
        with tempfile.NamedTemporaryFile() as tf:
            s3_object.download_fileobj(tf)
            tf.seek(0)

            line_count, insert_sum = import_into_elasticsearch(
                tf,
                es,
                max_epmc_metadata=self.max_epmc_metadata
            )

        self.log.info(
            'Elasticsearch has %d records (%d newly imported)',
            line_count['count'],
            insert_sum,
        )
