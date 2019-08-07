"""
Operator to run the web scraper on every organisation.
"""
import os
import logging

from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults

from policytool.airflow.safe_import import safe_import
from policytool.sentry import report_exception


logger = logging.getLogger(__name__)


class ParsePdfOperator(BaseOperator):
    """
    Pulls data from the dimensions.ai to a bucket in S3.

    Args:
        organisation: The organisation to pull documents from.
    """

    template_fields = (
        'dst_s3_key',
        'src_s3_dir',
    )

    @apply_defaults
    def __init__(self, organisation, src_s3_dir, dst_s3_key, *args, **kwargs):
        super(ParsePdfOperator, self).__init__(*args, **kwargs)
        self.organisation = organisation
        self.src_s3_dir = src_s3_dir
        self.dst_s3_key = dst_s3_key

    @report_exception
    def execute(self, context):
        with safe_import():
            from policytool.pdf_parser.main import parse_all_pdf

        os.environ.setdefault(
            'SCRAPY_SETTINGS_MODULE',
            'scraper.wsf_scraping.settings'
        )
        if not self.src_s3_dir.startswith('s3://'):
            raise ValueError
        if not self.dst_s3_key.startswith('s3://'):
            raise ValueError

        input_uri = 'manifest' + self.src_s3_dir
        output_uri = 'manifest' + self.dst_s3_key
        parse_all_pdf(input_uri, output_uri, self.organisation, 2)
