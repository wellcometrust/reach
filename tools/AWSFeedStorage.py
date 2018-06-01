import boto3
import logging
from datetime import datetime
from six.moves.urllib.parse import urlparse
from .dynamodbConnector import DynamoDBConnector
from scrapy.extensions.feedexport import BlockingFeedStorage
from botocore.exceptions import ClientError


class AWSFeedStorage(BlockingFeedStorage):
    """This feed storage will store the results in a json file, in a S3 bucket
    and will update the Dynamodb catalog table with the location, the timestamp
    and the name of the file.
    """

    def __init__(self, uri):
        """Initialise the Feed Storage, giving it AWS informations."""
        from scrapy.conf import settings

        self.logger = logging.getLogger(__name__)

        u = urlparse(uri)
        self.s3_file = u.path[1:]
        self.s3_bucket = settings['AWS_S3_BUCKET']
        self.s3 = boto3.client('s3')
        self.dynamodb = DynamoDBConnector()

    def _get_last_result(self):
        try:
            objs = self.s3.list_objects_v2(
                Bucket=self.s3_bucket,
                Prefix=self.s3_file
            ).get('Contents', [])
        except ClientError:
            self.logger.warning('Could not connect to s3 bucket.')
            return ''

        if not objs:
            self.logger.warning('Could not get last result file.')
            return ''

        last_added = [obj['Key'] for obj in sorted(
            objs,
            key=lambda obj: obj['LastModified']
        )][0]
        last_file = self.s3.get_object(
            Bucket=self.s3_bucket,
            Key=last_added
        )
        last_content = last_file.get('Body').read()

        return last_content.decode('utf-8', 'replace')

    def _store_in_thread(self, data_file):
        """This method will try to upload the file to S3, then to insert the
        file's related information into DynamoDB.
        """
        data_file.seek(0)
        date_tag = datetime.now().strftime('%Y%m%d')
        try:
            last_content = self._get_last_result()
            content = last_content + data_file.read().decode()
            filename = "{folders}/{file_datetag}.json".format(
                folders=self.s3_file,
                file_datetag=date_tag
            )
            self.s3.put_object(
                Body=content,
                Bucket=self.s3_bucket,
                Key=filename
            )
        except ClientError as e:
            self.logger.error('Couldn\'t upload the json file to s3: %s', e)
        else:
            self.dynamodb.insert_file_in_catalog(
                filename,
                '/'.join([self.s3_bucket, self.s3_file, filename]),
            )
