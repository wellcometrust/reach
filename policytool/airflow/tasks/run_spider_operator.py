"""
Operator to run the web scraper on every organisation.
"""
import os
import logging

from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from policytool.scraper.wsf_scraping.spiders.nice_spider import NiceSpider
from policytool.scraper.wsf_scraping.spiders.gov_spider import GovSpider
from policytool.scraper.wsf_scraping.spiders.msf_spider import MsfSpider
from policytool.scraper.wsf_scraping.spiders.unicef_spider import UnicefSpider
from policytool.scraper.wsf_scraping.spiders.who_iris_spider import (
    WhoIrisSpider
)
from policytool.scraper.wsf_scraping.spiders.parliament_spider import (
    ParliamentSpider
)
from policytool.sentry import report_exception
import policytool.scraper.wsf_scraping.settings


logger = logging.getLogger(__name__)

SPIDERS = {
    'who_iris': WhoIrisSpider,
    'nice': NiceSpider,
    'gov_uk': GovSpider,
    'msf': MsfSpider,
    'unicef': UnicefSpider,
    'parliament': ParliamentSpider,
}


class RunSpiderOperator(BaseOperator):
    """
    Pulls data from the dimensions.ai to a bucket in S3.

    Args:
        organisation: The organisation to pull documents from.
    """

    template_fields = ('dst_s3_dir',)

    @apply_defaults
    def __init__(self, organisation, dst_s3_dir, *args, **kwargs):
        super(RunSpiderOperator, self).__init__(*args, **kwargs)
        self.organisation = organisation
        self.dst_s3_dir = dst_s3_dir

    @report_exception
    def execute(self, context):
        if not self.dst_s3_dir.startswith('s3://'):
            raise ValueError('Invalid S3 url: %s' % self.dst_s3_dir)

        os.environ.setdefault(
            'SCRAPY_SETTINGS_MODULE',
            'policytool.scraper.wsf_scraping.settings'
        )
        policytool.scraper.wsf_scraping.settings.FEED_URI = \
            'manifest' + self.dst_s3_dir

        settings = get_project_settings()

        process = CrawlerProcess(settings)
        spider = SPIDERS[self.organisation]
        process.crawl(spider)
        process.start()
