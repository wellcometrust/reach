"""
Operator to run the get the latest scraped fulltexts from AWS S3.
"""

from policytool.airflow.hook.wellcome_s3_hook import WellcomeS3Hook
from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults
from elasticsearch import Elasticsearch

from policytool.elastic.import_fulltexts_s3 import (
    import_into_elasticsearch,
    clean_es,
)


class ESIndexFulltexts(BaseOperator):
    """ Download the latest scraped publications texts stored in S3 and index
    them with Elasticsearch.
    """

    template_fields = (
        'src_s3_key',
    )

    @apply_defaults
    def __init__(self, src_s3_key, es_host, organisation, es_port=9200,
                 max_publication_number=None, aws_conn_id='aws_default',
                 *args, **kwargs):
        """
        Args:
            src_s3_key: S3 URL for the json.gz output file.
            es_host: the hostname of elasticsearch database.
            es_port: the port of elasticsearch database. Default to 9200.
            max_publication_number: Maximum number of fulltexts to process.
            aws_conn_id: Aws connection name.
        """

        super().__init__(*args, **kwargs)

        if not src_s3_key.endswith('.json.gz'):
            raise ValueError('src_s3_key must end in .json.gz')

        self.src_s3_key = src_s3_key
        self.es_host = es_host
        self.es_port = es_port
        self.organisation = organisation
        self.aws_conn_id = aws_conn_id
        self.max_publication_number = max_publication_number

    def execute(self, context):

        es = Elasticsearch([{'host': self.es_host, 'port': self.es_port}])
        s3 = WellcomeS3Hook()

        # TODO: implement skipping mechanism
        clean_es(es)

        if self.max_publication_number:
            self.log.info(
                'Getting %s pubs from %s',
                self.max_publication_number,
                self.src_s3_key,
            )
        else:
            self.log.info(
                'Getting %s pubs from %s',
                'all',
                self.src_s3_key,
            )

        s3_file = s3.get_key(self.src_s3_key)

        line_count, insert_sum = import_into_elasticsearch(
            s3_file,
            es,
            self.organisation,
            max_publication_number=self.max_publication_number
        )

        self.log.info(
            'Elasticsearch has %d records (%d newly imported)',
            line_count['count'],
            insert_sum,
        )
