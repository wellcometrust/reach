"""
Operator to run the web scraper on every organisation.
"""
import os
import logging

from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults

from reach.airflow.safe_import import safe_import
from reach.sentry import report_exception


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

    KEYWORD_SEARCH_CONTEXT = 2

    @apply_defaults
    def __init__(self, organisation, src_s3_dir, dst_s3_key, *args, **kwargs):
        super(ParsePdfOperator, self).__init__(*args, **kwargs)
        self.organisation = organisation
        self.src_s3_dir = src_s3_dir
        self.dst_s3_key = dst_s3_key

    @report_exception
    def execute(self, context):
        with safe_import():
            import reach.pdf_parser.main as pdf_parser_main

        os.environ.setdefault(
            'SCRAPY_SETTINGS_MODULE',
            'scraper.wsf_scraping.settings'
        )
        if not self.src_s3_dir.startswith('s3://'):
            raise ValueError
        if not self.dst_s3_key.startswith('s3://'):
            raise ValueError

        input_uri = 'manifest' + self.src_s3_dir
        pdf_parser_main.parse_all_pdf(
            self.organisation,
            input_uri,
            self.dst_s3_key,
        )
