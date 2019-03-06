"""
Operator to run the web scraper on every organisation.
"""
import os
import logging
import scraper.wsf_scraping.settings

from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from scraper.wsf_scraping.spiders.who_iris_spider import WhoIrisSpider
from scraper.wsf_scraping.spiders.nice_spider import NiceSpider
from scraper.wsf_scraping.spiders.gov_spider import GovSpider
from scraper.wsf_scraping.spiders.msf_spider import MsfSpider
from scraper.wsf_scraping.spiders.unicef_spider import UnicefSpider
from scraper.wsf_scraping.spiders.parliament_spider import ParliamentSpider


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

    @apply_defaults
    def __init__(self, organisation, *args, **kwargs):
        super(RunSpiderOperator, self).__init__(*args, **kwargs)
        self.organisation = organisation

    def execute(self, context):
        os.environ.setdefault(
            'SCRAPY_SETTINGS_MODULE',
            'scraper.wsf_scraping.settings'
        )
        path = os.path.join(
            'datalabs-data',
            'airflow',
            'output',
            'policytool-scrape',
            'scraper-{organisation}'.format(
                organisation=self.organisation
            ),
        )
        scraper.wsf_scraping.settings.FEED_URI = 'manifests3://{path}'.format(
            path=path
        )

        settings = get_project_settings()
        for key in sorted(settings):
            print(key, settings[key])

        process = CrawlerProcess(settings)
        spider = SPIDERS[self.organisation]
        process.crawl(spider)
        process.start()
