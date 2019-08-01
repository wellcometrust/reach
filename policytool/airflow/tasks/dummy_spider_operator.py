"""
Operator for scraping 10 articles from every organisation as a test.
"""

import json
import os
import logging

from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import scrapy.signals

from policytool.sentry import report_exception
from policytool.scraper.wsf_scraping import feed_storage
from policytool.scraper.wsf_scraping.spiders.who_iris_spider import WhoIrisSpider
from policytool.scraper.wsf_scraping.spiders.nice_spider import NiceSpider
from policytool.scraper.wsf_scraping.spiders.gov_spider import GovSpider
from policytool.scraper.wsf_scraping.spiders.msf_spider import MsfSpider
from policytool.scraper.wsf_scraping.spiders.unicef_spider import UnicefSpider
from policytool.scraper.wsf_scraping.spiders.parliament_spider import ParliamentSpider
import policytool.scraper.wsf_scraping.settings


SPIDERS = {
    'who_iris': WhoIrisSpider,
    'nice': NiceSpider,
    'gov_uk': GovSpider,
    'msf': MsfSpider,
    'unicef': UnicefSpider,
    'parliament': ParliamentSpider,
}


class DummySpiderOperator(BaseOperator):
    """
    Pulls data from the dimensions.ai to a bucket in S3.

    Args:
        organisation: The organisation to pull documents from.
    """

    template_fields = ('dst_s3_dir',)

    @apply_defaults
    def __init__(self, organisation, dst_s3_dir, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.organisation = organisation
        self.dst_s3_dir = dst_s3_dir
        self.dst_s3_dir = dst_s3_dir

        self.item_count = None
        self.scraper_errors = None


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


    @report_exception
    def execute(self, context):
        # Initialise settings for a limited scraping
        os.environ.setdefault(
            'SCRAPY_SETTINGS_MODULE',
            'policytool.scraper.wsf_scraping.settings'
        )

        if not self.dst_s3_dir.startswith('s3://'):
            raise ValueError('Invalid S3 url: %s' % self.dst_s3_dir)

        # This monkey-patching only works because Airflow shells out to
        # a new Python interpreter for every task it runs. It thus *must*
        # remain inside execute(), so other code paths don't touch it.
        policytool.scraper.wsf_scraping.settings.MAX_ARTICLE = 10
        policytool.scraper.wsf_scraping.settings.WHO_IRIS_YEARS = [2018]

        policytool.scraper.wsf_scraping.settings.FEED_URI = \
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
            self.logger.error(
                'DummySpiderOperator: scrapy signaled %d errors:',
                len(scraper_errors)
            )
            for tup in self.scraper_errors:
                logging.error('DummySpiderOperator: %r', tup)
            raise Exception(
                "%d errors occurred during scrape" %
                len(scraper_errors)
            )
