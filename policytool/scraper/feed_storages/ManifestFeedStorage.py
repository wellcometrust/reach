import logging

from scraper.wsf_scraping.storage import S3Storage, LocalStorage
from six.moves.urllib.parse import urlparse
from scrapy.extensions.feedexport import BlockingFeedStorage


class ManifestFeedStorage(BlockingFeedStorage):
    """This FeedStorage is given the informations about the pdf files scraped
    in the pipeline. It processes this information to update the manifest file
    in amazon s3. the PDF files are saved to s3 in the pipeline.py file.
    """

    def __init__(self, uri):
        """Initialise the Feed Storage with the feed uri."""
        self.logger = logging.getLogger(__name__)
        self.parsed_url = urlparse(uri)

    def open(self, spider):
        """The FeedStorage is opened by scrapy autmatically to receive
        items returned by the pipeleine. This methos initialise the object with
        a file system backend and a spider name (organisation).

        Should always return a class object.
        """
        path = self.parsed_url.path.replace('%(name)s', spider.name)
        if self.parsed_url.scheme == 'manifests3':
            self.storage = S3Storage(path, spider.name)
        else:
            self.storage = LocalStorage(path, spider.name)
        return super(ManifestFeedStorage, self).open(spider)

    def _store_in_thread(self, data_file):
        """This method is called once the process is finished, and will try
        to upload a manifest file file to S3.
        """
        self.storage.update_manifest(data_file)
