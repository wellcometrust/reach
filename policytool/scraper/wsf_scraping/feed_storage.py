import logging

from six.moves.urllib.parse import urlparse
from scrapy.extensions.feedexport import BlockingFeedStorage
from twisted.internet import reactor
from twisted.internet import threads

from .file_system import S3FileSystem, LocalFileSystem
from policytool.sentry import report_exception

manifest_storage_error = object()

class ManifestFeedStorage(BlockingFeedStorage):
    """This FeedStorage is given the informations about the pdf files scraped
    in the pipeline. It processes this information to update the manifest file
    in amazon s3. the PDF files are saved to s3 in the pipeline.py file.
    """

    def __init__(self, uri):
        """Initialise the Feed Storage with the feed uri."""
        self.logger = logging.getLogger(__name__)
        self.parsed_url = urlparse(uri)
        self.spider = None

    def open(self, spider):
        """The FeedStorage is opened by scrapy autmatically to receive
        items returned by the pipeleine. This methos initialise the object with
        a file system backend and a spider name (organisation).

        Should always return a class object.
        """
        self.spider = spider
        path = self.parsed_url.path.replace('%(name)s', spider.name)
        if self.parsed_url.scheme == 'manifests3':
            self.file_system = S3FileSystem(
                path,
                spider.name,
                self.parsed_url.netloc
            )
        else:
            self.file_system = LocalFileSystem(path, spider.name)
        return super(ManifestFeedStorage, self).open(spider)

    @report_exception
    def _store_in_thread(self, data_file):
        """
        Uploads our manifest file to S3.

        Called in Twisted's thread pool using
        twisted.internet.deferToThread. Thus the explicit exception
        reporting above.
        """
        self.logger.info('Updating the manifest at {bucket}/{uri}'.format(
            bucket=self.parsed_url.netloc,
            uri=self.parsed_url.path,
        ))
        try:
            self.file_system.update_manifest(data_file)
        except Exception as e:
            # If it went bad, we need to inform the spider back in
            # Twisted space, so that eventually the calling airflow task
            # can find out, too.
            self.logger.error('ManifestFeedStorage error: %s', e)
            result = threads.blockingCallFromThread(
                reactor,
                self.spider.crawler.signals.send_catch_log,
                signal=manifest_storage_error,
                exception=e
            )
            self.logger.info('send_catch_log: %s', result)
            raise
