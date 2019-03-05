import boto3
import os
import hashlib
import logging
import json
from abc import ABC, abstractmethod
from botocore.exceptions import ClientError


def get_file_hash(file_path):
    """Return the md5 hash of a file."""
    BLOCKSIZE = 65536
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        while True:
            buf = f.read(BLOCKSIZE)
            if not buf:
                break
            hasher.update(buf)
    return hasher.hexdigest()


class FileSystem(ABC):

    @abstractmethod
    def save(self, body, file_hash):
        """Saves the given file to a storage medium.
        Args:
            - body: The binary file body.
            - hash: The md5 digest of the file.
        Returns:
            - path: The full path of the saved file.
        """
        return

    @abstractmethod
    def get_manifest(self):
        """Get the last manifest for an organisation from S3.

        Args:
            - organisation: A string representing the name of the organisation.
        """
        return

    @abstractmethod
    def update_manifest(self, data_file):
        """Get the current manifest from the storage and update it.

        Args:
            - data_file: The file object sent by Scrapy's feed storage.
        """
        return

    @abstractmethod
    def get(self, file_hash):
        """Get the file matching the given hash from the storage.

        Args:
            - file_hash: The md5 digest of the file to retrieve.
        """
        return


class S3FileSystem(FileSystem):
    def __init__(self, path, organisation, bucket):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.client = boto3.client('s3')
        self.bucket = bucket
        self.prefix = path[1:]
        self.organisation = organisation

    def save(self, body, file_hash):

        key = os.path.join(
            self.prefix,
            'pdf',
            file_hash[:2],
            file_hash,
        )
        self.logger.debug('Writing {key} to S3'.format(key=key))

        try:
            self.client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=body,
            )
        except ClientError as e:
            raise e

    def get_manifest(self):
        key = os.path.join(
            self.prefix,
            'policytool-scrape--scraper-{organisation}.json'.format(
                organisation=self.organisation,
            ),
        )
        try:
            response = self.client.get_object(
                Bucket=self.bucket,
                Key=key,
            )
            if response.get('Body'):
                return json.loads(response['Body'].read())
            else:
                return dict()
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return dict()
            else:
                raise

    def update_manifest(self, data_file):
        current_manifest = self.get_manifest()
        data_file.seek(0)
        for row in data_file:
            item = json.loads(row)
            hash_list = current_manifest.get(item['hash'][:2], None)
            if hash_list:
                if item['hash'] not in hash_list:
                    hash_list.append(item['hash'])
            else:
                current_manifest[item['hash'][:2]] = [item['hash']]
        key = os.path.join(
            self.prefix,
            'policytool-scrape--scraper-{organisation}.json'.format(
                organisation=self.organisation,
            ),
        )
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=json.dumps(current_manifest).encode('utf-8')
        )

    def get(self, file_hash):
        prefix = os.path.join(self.path, file_hash[:2])
        response = self.client.get_object(
            Bucket=self.bucket,
            Prefix=prefix,
            Key=file_hash,
        )
        if response.get('Body'):
            return json.loads(response['Body'].read())
        else:
            return {}


class LocalFileSystem(FileSystem):
    def __init__(self, path, organisation):
        self.path = path
        self.organisation = organisation

    def save(self, body, file_hash):
        prefix = os.path.join(
            self.path,
            'pdf',
            file_hash[:2],
        )
        if not os.path.exists(prefix):
            os.makedirs(prefix, exist_ok=True)
        with open(os.path.join(prefix, file_hash), 'wb') as pdf_file:
            pdf_file.write(body.encode('utf-8'))

    def get_manifest(self):
        key = 'policytool-scrape--scraper-{organisation}.json'.format(
            organisation=self.organisation,
        )
        path = os.path.join(self.path, key)
        if os.path.isfile(path):
            with open(os.path.join(self.path, key), 'r') as manifest:
                return json.load(manifest)
        else:
            return {}

    def update_manifest(self, data_file):
        current_manifest = self.get_manifest()
        key = 'policytool-scrape--scraper-{organisation}.json'.format(
            organisation=self.organisation,
        )
        data_file.seek(0)
        for row in data_file:
            item = json.loads(row)
            hash_list = current_manifest.get(item['hash'][:2], None)
            if hash_list:
                if item['hash'] not in hash_list:
                    hash_list[item['hash']] = item
            else:
                current_manifest[item['hash'][:2]] = {item['hash']: item}
        with open(os.path.join(self.path, key), 'w') as manifest_file:
            manifest_file.write(json.dumps(current_manifest))

    def get(self, file_hash):
        key = 'policytool-scrape--scraper-{organisation}.json'.format(
            organisation=self.organisation,
        )
        path = os.path.join(self.path, file_hash[:2], file_hash)
        if os.path.isfile(path):
            with open(os.path.join(self.path, key), 'rb') as pdf:
                return pdf.read()
        else:
            return {}
