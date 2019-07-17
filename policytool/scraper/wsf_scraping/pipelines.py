# -*- coding: utf-8 -*-
import os
import logging
from urllib.parse import urlparse
from scrapy.utils.project import get_project_settings
from .file_system import S3FileSystem, LocalFileSystem, get_file_hash
from scrapy.exceptions import DropItem


class WsfScrapingPipeline(object):
    def __init__(self, organisation):
        """Initialise the pipeline, giving it access to the settings, keywords
           and creating the folder in which to store pdfs if stored locally.
        """

        self.settings = get_project_settings()
        uri = self.settings['FEED_URI'].replace('%(name)s', organisation)

        # Initialize logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.logger.info(
            'Pipeline initialized FEED_CONFIG=%s',
            self.settings.get('FEED_CONFIG'),
        )
        self.setup_storage(uri, organisation)
        self.manifest = self.storage.get_manifest()

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.spider.name)

    def setup_storage(self, url, organisation):
        """Take the output url and set the right feed storage for the pdf.

        Sets the storage system in use for the pipeline in the following:
          * S3FileSystem: Store the pdfs in Amazon S3.
          * LocalFileSystem: Store the pdfs in a local directory.

        Args:
            - url: A string reprensenting the location to store the pdf files.
        """
        parsed_url = urlparse(url)
        scheme = parsed_url.scheme
        if scheme == 'manifests3':
            self.logger.debug('Using S3 File system')
            self.storage = S3FileSystem(
                parsed_url.path,
                organisation,
                parsed_url.netloc
            )
        else:
            self.logger.debug('Using Local File System')
            self.storage = LocalFileSystem(parsed_url.path, organisation)

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

        in_manifest = self.is_in_manifest(item['hash'])

        if not in_manifest:
            path = os.path.join(
                'pdf',
                item['hash'][:2],
            )
            with open(item['pdf'], 'rb') as pdf:
                self.storage.save(pdf, path, item['hash'] + '.pdf')
        else:
            raise DropItem(
                'This pdf is already in the manifest file.'
            )

        return item
