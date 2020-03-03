#!/usr/bin/env python3
"""
Operator to run the web scraper on every organisation.
"""
import os
import logging
import argparse
from urllib.parse import urlparse

from hooks.sentry import report_exception
from hooks.s3hook import S3Hook

from pdf_parser import main as pdf_parser_main

logger = logging.getLogger(__name__)


ORGS = [
    'who_iris',
    'nice',
    'gov_uk',
    'msf',
    'unicef',
    'parliament',
    'acme',
]


class ParsePdfOperator:
    """
    Pulls data from the dimensions.ai to a bucket in S3.

    Args:
        organisation: The organisation to pull documents from.
    """

    def __init__(self, organisation, src_s3_dir, dst_s3_key, *args, **kwargs):
        super(ParsePdfOperator, self).__init__(*args, **kwargs)
        self.organisation = organisation
        self.src_s3_dir = src_s3_dir
        self.dst_s3_key = os.path.join(dst_s3_key, f"{organisation}.json.gz")

        self.client = S3Hook()

    @report_exception
    def execute(self):
        os.environ.setdefault(
            'SCRAPY_SETTINGS_MODULE',
            'scraper.wsf_scraping.settings'
        )
        if not self.src_s3_dir.startswith('s3://'):
            raise ValueError
        if not self.dst_s3_key.startswith('s3://'):
            raise ValueError

        pdf_parser_main.parse_all_pdf(
            self.organisation,
            self.src_s3_dir,
            self.dst_s3_key,
        )


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(
        description='Run a web scraper for a given organisation and writes the'
                    ' results to the given S3 path.'
    )
    arg_parser.add_argument(
        'src_s3_dir',
        help='The source path to s3.'
    )
    arg_parser.add_argument(
        'dst_s3_key',
        help='The destination path to s3.'
    )
    arg_parser.add_argument(
        'organisation',
        choices=ORGS,
        help='The organisation to scrape.'
    )

    args = arg_parser.parse_args()

    parser = ParsePdfOperator(
        args.organisation,
        args.src_s3_dir,
        args.dst_s3_key,
    )

    parser.execute()
