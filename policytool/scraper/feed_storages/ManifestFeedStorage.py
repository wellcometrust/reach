import logging

from scraper.wsf_scraping.storage import S3Storage, LocalStorage
from six.moves.urllib.parse import urlparse
from scrapy.extensions.feedexport import BlockingFeedStorage


class ManifestFeedStorage(BlockingFeedStorage):
    """Stores Scrapy feed results as json files in S3.
    """

    def __init__(self, uri):
        """Initialise the Feed Storage, giving it AWS informations."""
        self.logger = logging.getLogger(__name__)
        self.parsed_url = urlparse(uri)

    def open(self, spider):
        path = self.parsed_url.path.replace('%(name)s', spider.name)
        if self.parsed_url.scheme == 's3':
            self.storage = S3Storage(path, spider.name)
        else:
            self.storage = LocalStorage(path, spider.name)
        return super(ManifestFeedStorage, self).open(spider)

    def _store_in_thread(self, data_file):
        """This method will try to upload the file to S3.
        """
        self.storage.update_manifest(data_file)
