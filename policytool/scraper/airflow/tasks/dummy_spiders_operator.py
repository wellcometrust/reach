"""
Operators for fetching data from dimensions.ai.
"""


import os
import logging
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


class DummySpidersOperator(BaseOperator):
    """
    Pulls data from the dimensions.ai to a bucket in S3.

    Args:
        data_source: 'grants' or 'publications'
        year: year for which to pull data (int)
        s3_key: destination url (s3://BUCKET_NAME/KEY_NAME)
        aws_conn_id: AWS connection name
        dimensions_conn_id: dimensions.ai connection name
        replace: True if task should overwrite existing s3 key
    """

    @apply_defaults
    def __init__(self, organisation, *args, **kwargs):
        super(DummySpidersOperator, self).__init__(*args, **kwargs)
        self.organisation = organisation

    def execute(self, context):

        # Initialise settings for a limited scraping
        settings = get_project_settings()
        settings.set('MAX_ARTICLE', 10)
        settings.set('WHO_IRIS_YEARS', [2018])
        settings.set('DATABASE_URL', os.environ['DATABASE_URL'])

        process = CrawlerProcess(settings)
        spider = SPIDERS[self.organisation]
        process.crawl(spider)
        process.start()
