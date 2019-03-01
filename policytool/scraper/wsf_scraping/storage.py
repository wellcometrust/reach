import boto3
import os
import hashlib
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


class Storage(ABC):

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


class S3Storage(Storage):
    def __init__(self, path, organisation):
        self.client = boto3.client('s3')
        self.bucket = path.split('/')[0]
        self.prefix = path.split('/')[1:]
        self.organisation = organisation

    def save(self, body, file_hash):

        # The prefix is the path concatenated with 'pdf' and a directory named
        # from the first two characters of the file's md5 digest.
        prefix = os.path.join(
            self.prefix,
            'pdf',
            file_hash[:2],
        )

        try:
            self.client.put_object(
                Bucket=self.bucket,
                Prefix=prefix,
                Key=file_hash,
                Body=body,
            )
        except ClientError as e:
            raise e

    def get_manifest(self):
        response = self.client.get_object(
            Bucket=self.bucket,
            Prefix=self.prefix,
            Key='policytool-scrape--scraper-{organisation}.json'.format(
                organisation=self.organisation,
            ),
        )
        if response.get('Body'):
            return json.loads(response['Body'].read())
        else:
            return {}

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

        self.client.put_object(
            Bucket=self.bucket,
            Prefix=self.prefix,
            Key='policytool-scrape--scraper-{organisation}.json'.format(
                organisation=self.organisation,
            ),
            Body=current_manifest.encode('utf-8')
        )


class LocalStorage(Storage):
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
                if item['hash'] not in hash_list.keys():
                    hash_list[item['hash']] = item
            else:
                current_manifest[item['hash'][:2]] = {item['hash']: item}
        with open(os.path.join(self.path, key), 'w') as manifest_file:
            manifest_file.write(json.dumps(current_manifest))
