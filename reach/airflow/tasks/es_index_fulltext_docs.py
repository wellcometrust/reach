"""
Operator to run the get the latest scraped fulltexts from AWS S3.
"""
import tempfile

from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults

from reach.airflow.hook.wellcome_s3_hook import WellcomeS3Hook
from reach.elastic import fulltext_docs
import reach.elastic.common


class ESIndexFulltextDocs(BaseOperator):
    """ Download the latest scraped publications texts stored in S3 and index
    them with Elasticsearch.
    """

    template_fields = (
        'src_s3_key',
    )

    @apply_defaults
    def __init__(self, src_s3_key, es_host, organisation, es_port=9200,
                 max_items=None, aws_conn_id='aws_default',
                 es_index=None, *args, **kwargs):
        """
        Args:
            src_s3_key: S3 URL for the json.gz output file.
            es_host: the hostname of elasticsearch database.
            es_port: the port of elasticsearch database. Default to 9200.
            max_items: Maximum number of fulltexts to process.
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
        self.max_items = max_items
        self.es_index = es_index

    def execute(self, context):
        es = reach.elastic.common.connect(
            self.es_host, self.es_port)
        s3 = WellcomeS3Hook()

        # TODO: implement skipping mechanism
        fulltext_docs.clean_es(es, self.es_index, self.organisation)

        if self.max_items:
            self.log.info(
                'Getting %s pubs from %s',
                self.max_items,
                self.src_s3_key,
            )
        else:
            self.log.info(
                'Getting %s pubs from %s',
                'all',
                self.src_s3_key,
            )

        s3_object = s3.get_key(self.src_s3_key)
        with tempfile.NamedTemporaryFile() as tf:
            s3_object.download_fileobj(tf)
            tf.seek(0)
            count = fulltext_docs.insert_file(
                tf,
                es,
                self.organisation,
                max_items=self.max_items,
                es_index=self.es_index,
            )
        self.log.info('import complete count=%d', count)
