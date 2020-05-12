#!/usr/bin/env python3
"""
Operator for scraping articles from every organisation.
"""

import json
import os
import argparse
import datetime
import sys
import logging

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import scrapy.signals

from wsf_scraping import feed_storage
from wsf_scraping.spiders.who_iris_spider import WhoIrisSpider
from wsf_scraping.spiders.nice_spider import NiceSpider
from wsf_scraping.spiders.gov_spider import GovSpider
from wsf_scraping.spiders.msf_spider import MsfSpider
from wsf_scraping.spiders.unicef_spider import UnicefSpider
from wsf_scraping.spiders.parliament_spider import ParliamentSpider
from wsf_scraping.spiders.acme_spider import AcmeSpider
import wsf_scraping.settings

from hooks.sentry import report_exception


SPIDERS = {
    'who_iris': WhoIrisSpider,
    'nice': NiceSpider,
    'gov_uk': GovSpider,
    'msf': MsfSpider,
    'unicef': UnicefSpider,
    'parliament': ParliamentSpider,
    'acme': AcmeSpider,
}


class SpiderOperator:
    """
    Pulls data from the dimensions.ai to a bucket in S3.

    Args:
        organisation: The organisation to pull documents from.
    """

    def __init__(self, organisation, dst_s3_dir,
                 item_years, item_max):

        self.organisation = organisation
        self.dst_s3_dir = dst_s3_dir

        self.item_count = None
        self.scraper_errors = None
        self.item_max = item_max
        self.item_years = item_years

        self.log = logging.getLogger(__name__)

    def on_item_scraped(self, item, response):
        """ Increments our count of items for reporting/future metrics. """
        self.item_count += 1

    def on_item_error(self, item, response, failure):
        """
        Records Scrapy item_error signals; these fire automatically if
        exceptions occur while saving items in the pipeline.
        """
        self.scraper_errors.append(
            ('item_error', item, response, failure)
        )

    def on_manifest_storage_error(self, exception):
        """
        Records our feed storage's error signal, as would occur when
        exceptions occur while saving the manifest to S3.
        """
        self.scraper_errors.append(
            ('manifest_storage_error', exception)
        )

    def execute(self):
        # Initialise settings for a limited scraping
        os.environ.setdefault(
            'SCRAPY_SETTINGS_MODULE',
            'wsf_scraping.settings'
        )

        if not self.dst_s3_dir.startswith('s3://'):
            raise ValueError('Invalid S3 url: %s' % self.dst_s3_dir)

        # This monkey-patching only works because Airflow shells out to
        # a new Python interpreter for every task it runs. It thus *must*
        # remain inside execute(), so other code paths don't touch it.
        wsf_scraping.settings.MAX_ARTICLE = self.item_max
        wsf_scraping.settings.WHO_IRIS_YEARS = \
            self.item_years

        wsf_scraping.settings.FEED_URI = \
            'manifest' + self.dst_s3_dir

        settings = get_project_settings()
        self.log.info(
            "scrapy settings: %s",
            json.dumps(
                {k: v for k, v in settings.items()
                 if isinstance(v, (str, int, float, bool))}
            )
        )

        process = CrawlerProcess(settings, install_root_handler=False)
        spider = SPIDERS[self.organisation]
        crawler = process.create_crawler(spider)

        self.item_count = None
        self.scraper_errors = []
        crawler.signals.connect(
            self.on_item_error,
            signal=scrapy.signals.item_error)
        crawler.signals.connect(
            self.on_manifest_storage_error,
            signal=feed_storage.manifest_storage_error)

        process.crawl(crawler)  # starts reactor
        process.start()  # waits for reactor to finish

        if self.scraper_errors:
            scraper_errors = self.scraper_errors  # put into local for sentry
            self.log.error(
                'SpiderOperator: scrapy signaled %d errors:',
                len(scraper_errors)
            )
            for tup in self.scraper_errors:
                self.log.error('DummySpiderOperator: %r', tup)
            raise Exception(
                "%d errors occurred during scrape" %
                len(scraper_errors)
            )


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(
        description='Run a web scraper for a given organisation and writes the'
                    ' results to the given S3 path.'
    )
    arg_parser.add_argument(
        'dst_s3_dir',
        help='The destination path to s3.'
    )
    arg_parser.add_argument(
        'organisation',
        choices=SPIDERS.keys(),
        help='The organisation to scrape.'
    )
    arg_parser.add_argument(
        '--max-items',
        type=int,
        help='The number of documents to scrape.',
        default=None
    )

    args = arg_parser.parse_args()

    spider = SpiderOperator(
        args.organisation,
        args.dst_s3_dir,
        list(range(2012, datetime.datetime.now().year + 1)),
        args.max_items,
    )

    spider.execute()

    sys.exit(0)
