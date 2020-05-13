# -*- coding: utf-8 -*-
import os
import logging
from urllib.parse import urlparse
from scrapy.utils.project import get_project_settings
from hooks.s3hook import S3Hook, get_file_hash, get_pdf_id
from scrapy.exceptions import DropItem


class WsfScrapingPipeline(object):
    def __init__(self, organisation):
        """Initialise the pipeline, giving it access to the settings, keywords
           and creating the folder in which to store pdfs if stored locally.
        """

        self.settings = get_project_settings()
        self.uri = self.settings['FEED_URI'].replace('%(name)s', organisation)

        # Initialize logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.logger.info(
            'Pipeline initialized FEED_CONFIG=%s',
            self.settings.get('FEED_CONFIG'),
        )
        self.storage = S3Hook()
        self.manifest = self.storage.get_manifest(self.uri, organisation)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.spider.name)

    def is_in_manifest(self, hash):
        """Check if a file hash is in the current manifest.

        Args:
            - hash: A 36 chars string repsenting the md5 digest of a file.
        Returns:
            - True if the file hash is in the manifest, else False.
        """
        if hash[:2] in self.manifest:
            if hash in self.manifest[hash[:2]]:
                return True
        return False

    def process_item(self, item, spider):
        """Process items sent by the spider.

        The returned items will then be sent to the FeedStorage, where they
        are stored in a temporary file and processed at the end of the process.

        Args:
            - item: The item returned by the spider.
            - spider: The spider from which the item id coming.
        Raises:
            - DropItem: If the pdf couldn't be saved, we want to drop the item.
        Returns:
            - item: The processed item, to be used in a feed storage.
        """

        if not item['pdf']:
            raise DropItem(
                'Empty filename, could not parse the pdf.'
            )
        item['hash'] = get_file_hash(item['pdf'])
        item['did'] = get_pdf_id(item['pdf'])

        in_manifest = self.is_in_manifest(item['hash'])

        if not in_manifest:
            dst_key = os.path.join(
                self.uri,
                'pdf',
                item['hash'][:2],
                item['hash'] + '.pdf',
            )
            with open(item['pdf'], 'rb') as pdf:
                self.storage.save(pdf, dst_key)

        # Remove the file to save storage
        os.unlink(item['pdf'])

        return item
