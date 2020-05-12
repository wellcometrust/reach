import boto3
import os
import hashlib
import logging
import json
import datetime
import subprocess
import re
from urllib.parse import urlparse

from botocore.exceptions import ClientError


ORGS = [
    'who_iris',
    'nice',
    'gov_uk',
    'msf',
    'unicef',
    'parliament',
    'acme',
]


def get_file_hash(file_path):
    """ Return both possible IDs for a given document
    in the form (<pdf DocumentId>, <file hash>)
    """

    BLOCKSIZE = 65536
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        while True:
            buf = f.read(BLOCKSIZE)
            if not buf:
                break
            hasher.update(buf)

    return hasher.hexdigest()


def get_pdf_id(document):
    """ Get PDF metadata/document data using
    the `pdfinfo` command line utility in poppler

    Args:
        document: (file) the file to parse
    """
    cmd = [
        'pdfinfo',
        '-meta',
        document
    ]

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    reg_xmp = re.compile("<xmpMM:DocumentID>(.*)<\/xmpMM:DocumentID>")
    reg_xap = re.compile("<xapMM:DocumentID>(.*)<\/xapMM:DocumentID>")

    if result.returncode == 0:
        # info scrape succeeded
        # skip any non-unicode characters
        string_data = result.stdout.decode("utf-8", 'ignore')

        item = reg_xmp.search(string_data)

        # key prefixes can exist as xapMM or xmpMM; not sure why
        # TODO: Look into this
        if item is None:
            item = reg_xap.search(string_data)

        if item is not None:
            if item.group(1) is not None:
                ident = item.group(1)
                return ident.split(":")[-1]
            else:
                return None
        else:
            return None

    return None


class S3Hook(object):
    """
    (Blocking!) wrapper for writing things to S3.
    """
    def __init__(self):
        logging.basicConfig()
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.client = boto3.resource('s3')
        self.start_time = datetime.datetime.now()

    def parse_s3_url(self, key):
        """Takes a url to an s3 location and returns the bucket and the path"""
        parsed_key = urlparse(key)
        # Scrapy need to use manifests3 style urls because s3:// is a defaut
        # value for its non-overridable S3FeedStorage.
        if parsed_key.scheme not in ["s3", 'manifests3']:
            raise ValueError
        return parsed_key.netloc, parsed_key.path[1:]  # Remove leading `/`

    def save(self, body, dst_key):
        """Save a given body to an S3 location."""
        bucket, path = self.parse_s3_url(dst_key)
        self.logger.debug('Writing {key} to S3'.format(key=dst_key))
        try:
            bucket = self.client.Bucket(bucket)
            bucket.put_object(
                Key=path,
                Body=body
            )
        except ClientError as e:
            raise e

    def save_fileobj(self, fileobj, dst_key):
        """Save a fileobj to an S3 location."""
        bucket, path = self.parse_s3_url(dst_key)
        try:
            bucket = self.client.Bucket(bucket)
            bucket.upload_fileobj(
                Key=path,
                Fileobj=fileobj
            )
        except ClientError as e:
            raise e

    def get_manifest(self, src_key, organisation):
        """Get the current manifest for an organisation at a given key in s3.
        """
        bucket, path = self.parse_s3_url(src_key)
        manifest_key = os.path.join(
            path,
            'reach-scrape--scraper-{organisation}.json'.format(
                organisation=organisation,
            ),
        )
        try:
            self.logger.info(
                'Trying to get {manifest_key}'.format(
                    manifest_key=manifest_key
                )
            )
            s3_object = self.client.Object(bucket, manifest_key)
            response = s3_object.get()
            return json.loads(response['Body'].read())

        except ClientError as e:
            # If no manifest is found, just sends an empty dict to fill
            if e.response['Error']['Code'] == 'NoSuchKey':
                return {}
            raise e

    def update_manifest(self, data_file, dst_key, organisation=""):
        """Update an organisation's manifest at a given S3 location."""
        current_manifest = self.get_manifest(dst_key, organisation)

        metadata = {}
        metadata['organisation'] = organisation
        metadata['start-time'] = \
            self.start_time.isoformat()
        metadata['stop-time'] = \
            datetime.datetime.now().isoformat()

        data_file.seek(0)

        # If the manifest has no content yet, let's create it
        content = current_manifest.get('content', {})
        data = current_manifest.get('data', {})
        for row in data_file:
            item = json.loads(row)
            hash_list = content.get(item['hash'][:2], None)
            if hash_list:
                if item['hash'] not in hash_list:
                    hash_list.append(item['hash'])
            else:
                content[item['hash'][:2]] = [item['hash']]

            # Update the hash entry with any new information
            # coming from the page
            data[item['hash']] = dict(item)

        bucket, path = self.parse_s3_url(dst_key)
        key = os.path.join(
            path,
            'reach-scrape--scraper-{organisation}.json'.format(
                organisation=organisation,
            ),
        )
        self.logger.info('Writing {manifest} to s3'.format(manifest=key))
        bucket = self.client.Bucket(bucket)
        bucket.put_object(
            Key=key,
            Body=json.dumps(
                {'metadata': metadata, 'content': content, 'data': data}
            ).encode('utf-8')
        )

    def get(self, src_key):
        """Get the object at the specified location in S3"""
        try:
            self.logger.info(src_key)
            bucket, path = self.parse_s3_url(src_key)
            s3_object = self.client.Object(bucket, path)
            response = s3_object.get()
            if response.get('Body'):
                return response['Body']
        except ClientError as e:
            raise e

        return None

    def get_s3_object(self, src_key):
        """Return a raw S3 object from a given location."""
        try:
            self.logger.info(src_key)
            bucket, path = self.parse_s3_url(src_key)
            return self.client.Object(bucket, path)
        except ClientError as e:
            raise e

        return None

    def load_file(self, filename, dst_key, replace=False):
        bucket, path = self.parse_s3_url(dst_key)
        s3_object = self.client.Object(bucket, path)
        s3_object.upload_file(filename)
