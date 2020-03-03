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
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.client = boto3.client('s3')
        self.start_time = datetime.datetime.now()

    def save(self, body, dst_key, organisation=''):
        parsed_dst = urlparse(dst_key)
        self.logger.debug('Writing {key} to S3'.format(key=dst_key))
        try:
            self.client.put_object(
                Bucket=parsed_dst.netloc,
                Key=parsed_dst.path[1:],  # remove first /
                Body=body,
            )
        except ClientError as e:
            raise e

    def save_fileobj(self, fileobj, dst_key, organisation=''):
        parsed_dst = urlparse(dst_key)
        self.logger.info('FileSystem.save_fileobj: {key}', dst_key)
        self.client.upload_fileobj(
            Fileobj=fileobj,
            Bucket=parsed_dst.netloc,
            Key=parsed_dst.path[1:],  # remove first /
        )

    def get_manifest(self, src_key, organisation):
        parsed_src = urlparse(src_key)
        manifest_key = os.path.join(
            parsed_src.path,
            'reach-scrape--scraper-{organisation}.json'.format(
                organisation=organisation,
            ),
        )
        try:
            response = self.client.get_object(
                Bucket=parsed_src.netloc,
                Key=manifest_key,
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

    def update_manifest(self, data_file, dst_key, organisation=""):
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

        parsed_dst = urlparse(dst_key)
        key = os.path.join(
            parsed_dst.netloc,
            parsed_dst.path,
            'reach-scrape--scraper-{organisation}.json'.format(
                organisation=organisation,
            ),
        )
        self.client.put_object(
            Bucket=parsed_dst.netloc,
            Key=key[1:],  # remove first /
            Body=json.dumps(
                {'metadata': metadata, 'content': content, 'data': data}
            ).encode('utf-8')
        )

    def get(self, bucket, prefix, file_hash):
        try:
            key = os.path.join(
                prefix, 'pdf', file_hash[:2], file_hash + '.pdf')
            response = self.client.get_object(
                Bucket=bucket,
                Key=key,
            )
            if response.get('Body'):
                return response['Body']
        except ClientError as e:
            raise e

        return None
