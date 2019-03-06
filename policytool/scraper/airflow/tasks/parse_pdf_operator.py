"""
Operator to run the web scraper on every organisation.
"""
import os
import logging

from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults

from pdf_parser.main import parse_pdfs


logger = logging.getLogger(__name__)

RESOURCE_FILES = '/src/policytool/resources/'


class ParsePdfOperator(BaseOperator):
    """
    Pulls data from the dimensions.ai to a bucket in S3.

    Args:
        organisation: The organisation to pull documents from.
    """

    @apply_defaults
    def __init__(self, organisation, input_path, output_path, *args, **kwargs):
        super(ParsePdfOperator, self).__init__(*args, **kwargs)
        self.organisation = organisation
        self.input_path = input_path
        self.output_path = output_path

    def execute(self, context):
        os.environ.setdefault(
            'SCRAPY_SETTINGS_MODULE',
            'scraper.wsf_scraping.settings'
        )
        input = 'manifests3://{path}'.format(
            path=self.input_path,
        )
        output = 'manifests3://{path}'.format(
            path=self.output_path,
        )
        parse_pdfs(input, output, RESOURCE_FILES, self.organisation, 2)
