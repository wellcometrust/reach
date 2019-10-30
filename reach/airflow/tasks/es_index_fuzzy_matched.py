"""
Operator to index the latest fuzzy matched citations from AWS S3 to
Elasticsearch.
"""

import tempfile

from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults

from reach.airflow.hook.wellcome_s3_hook import WellcomeS3Hook
from reach.elastic import fuzzy_matched_citations
import reach.elastic.common


class ESIndexFuzzyMatchedCitations(BaseOperator):
    """ Download fuzzy matched citations stored in S3 and index them with
    Elasticsearch.
    """

    template_fields = (
        'src_s3_key',
    )

    @apply_defaults
    def __init__(self, src_s3_key, es_host, organisation,  es_port=9200,
                 item_limits=None, aws_conn_id='aws_default',
                 es_index=None, *args, **kwargs):
        """
        Args:
            src_s3_key: S3 URL for the json.gz output file.
            es_host: the hostname of elasticsearch database.
            es_port: the port of elasticsearch database. Default to 9200.
            item_limits: Maximum number of citations to process.
            aws_conn_id: Aws connection name.
        """

        super().__init__(*args, **kwargs)

        if not src_s3_key.endswith('.json.gz'):
            raise ValueError('src_s3_key must end in .json.gz')

        self.src_s3_key = src_s3_key
        self.es_host = es_host
        self.es_port = es_port
        self.aws_conn_id = aws_conn_id
        self.item_limits = item_limits
        self.es_index = es_index
        self.organisation = organisation

    def execute(self, context):
        es = reach.elastic.common.connect(
            self.es_host, self.es_port)
        s3 = WellcomeS3Hook()

        # TODO: implement skipping mechanism
        fuzzy_matched_citations.clean_es(es, self.es_index, self.organisation)

        self.log.info(
            'Getting %s pubs from %s',
            self.item_limits if self.item_limits else 'all',
            self.src_s3_key,
        )

        s3_object = s3.get_key(self.src_s3_key)
        with tempfile.NamedTemporaryFile() as tf:
            s3_object.download_fileobj(tf)
            tf.seek(0)
            count = fuzzy_matched_citations.insert_file(
                tf,
                es,
                org=self.organisation,
                max_items=self.item_limits,
                es_index=self.es_index,
            )
        self.log.info('execute: insert complete count=%d', count)
