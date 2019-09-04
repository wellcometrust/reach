import boto3
import os
import hashlib
import logging
import json
import datetime
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
        pass

    @abstractmethod
    def get_manifest(self):
        """Get the last manifest for an organisation from S3.

        Args:
            - organisation: A string representing the name of the organisation.
        """
        pass

    @abstractmethod
    def update_manifest(self, data_file):
        """Get the current manifest from the storage and update it.

        Args:
            - data_file: The file object sent by Scrapy's feed storage.
        """
        pass

    @abstractmethod
    def get(self, file_hash):
        """Get the file matching the given hash from the storage.
        Args:
            - file_hash: The md5 digest of the file to retrieve.
        """
        pass


class S3FileSystem(FileSystem):
    """
    (Blocking!) wrapper for writing things to S3.
    """
    def __init__(self, path, organisation, bucket):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.client = boto3.client('s3')
        self.bucket = bucket
        self.prefix = path[1:]
        self.organisation = organisation
        self.start_time = datetime.datetime.now()

    def save(self, body, path, filename):
        key = os.path.join(self.prefix, path, filename)
        self.logger.debug('Writing {key} to S3'.format(key=key))
        try:
            self.client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=body,
            )
        except ClientError as e:
            raise e

    def save_fileobj(self, fileobj, path, filename):
        key = os.path.join(self.prefix, path, filename)
        self.logger.info('FileSystem.save_fileobj: s3://%s/%s',
                         self.bucket, key)
        self.client.upload_fileobj(
            Fileobj=fileobj,
            Bucket=self.bucket,
            Key=key,
        )

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
                return {}
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return {}
            else:
                raise

    def update_manifest(self, data_file):
        current_manifest = self.get_manifest()

        metadata = {}
        metadata['organisation'] = self.organisation
        metadata['start-time'] = \
            self.start_time.isoformat()
        metadata['stop-time'] = \
            datetime.datetime.now().isoformat()

        data_file.seek(0)

        # If the manifest has no content yet, let's create it
        content = current_manifest.get('content', {})
        for row in data_file:
            item = json.loads(row)
            hash_list = content.get(item['hash'][:2], None)
            if hash_list:
                if item['hash'] not in hash_list:
                    hash_list.append(item['hash'])
            else:
                content[item['hash'][:2]] = [item['hash']]

        key = os.path.join(
            self.prefix,
            'policytool-scrape--scraper-{organisation}.json'.format(
                organisation=self.organisation,
            ),
        )
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=json.dumps(
                {'metadata': metadata, 'content': content}
            ).encode('utf-8')
        )

    def get(self, file_hash):
        try:
            key = os.path.join(
                self.prefix, 'pdf', file_hash[:2], file_hash + '.pdf')
            response = self.client.get_object(
                Bucket=self.bucket,
                Key=key,
            )
            if response.get('Body'):
                return response['Body']
        except ClientError as e:
            raise e

        return None


class LocalFileSystem(FileSystem):
    def __init__(self, prefix, organisation):
        self.prefix = prefix
        self.organisation = organisation

    def save(self, body, path, filename):
        prefix = os.path.join(
            self.prefix,
            path
        )
        if not os.path.exists(prefix):
            os.makedirs(prefix, exist_ok=True)
        with open(os.path.join(prefix, filename), 'wb') as pdf_file:
            pdf_file.write(body.encode('utf-8'))

    def get_manifest(self):
        key = 'policytool-scrape--scraper-{organisation}.json'.format(
            organisation=self.organisation,
        )
        path = os.path.join(self.prefix, key)
        if os.path.isfile(path):
            with open(os.path.join(self.prefix, key), 'r') as manifest:
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
        with open(os.path.join(self.prefix, key), 'w') as manifest_file:
            manifest_file.write(json.dumps(current_manifest))

    def get(self, file_hash):
        key = os.path.join(self.prefix, file_hash[:2], file_hash)

        if os.path.isfile(key):
            with open(os.path.join(self.prefix, key), 'rb') as pdf:
                return pdf
        else:
            return None
