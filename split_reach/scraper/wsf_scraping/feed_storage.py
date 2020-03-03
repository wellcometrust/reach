import logging

from scrapy.extensions.feedexport import BlockingFeedStorage
from twisted.internet import reactor
from twisted.internet import threads

from hooks.s3hook import S3Hook
from hooks.sentry import report_exception

manifest_storage_error = object()


class ManifestFeedStorage(BlockingFeedStorage):
    """This FeedStorage is given the informations about the pdf files scraped
    in the pipeline. It processes this information to update the manifest file
    in amazon s3. the PDF files are saved to s3 in the pipeline.py file.
    """

    def __init__(self, url):
        """Initialise the Feed Storage with the feed uri."""
        self.logger = logging.getLogger(__name__)
        self.dst_key_url = url
        self.spider = None

    def open(self, spider):
        """The FeedStorage is opened by scrapy autmatically to receive
        items returned by the pipeleine. This methos initialise the object with
        a file system backend and a spider name (organisation).

        Should always return a class object.
        """
        self.spider = spider
        self.file_system = S3Hook()
        return super(ManifestFeedStorage, self).open(spider)

    @report_exception
    def _store_in_thread(self, data_file):
        """
        Uploads our manifest file to S3.

        Called in Twisted's thread pool using
        twisted.internet.deferToThread. Thus the explicit exception
        reporting above.
        """
        self.logger.info('Updating the manifest at {dst_key_url}'.format(
            dst_key_url=self.dst_key_url,
        ))
        try:
            self.file_system.update_manifest(
                data_file,
                self.dst_key_url,
                self.spider.name
            )
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
