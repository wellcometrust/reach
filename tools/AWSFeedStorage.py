import boto3
import logging
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

        self.s3_bucket = settings['AWS_S3_BUCKET']
        self.s3_file = settings['AWS_S3_FILE_NAME']
        self.s3 = boto3.resource('s3')
        self.dynamodb = DynamoDBConnector()

    def _store_in_thread(self, data_file):
        """This method will try to upload the file to S3, then to insert the
        file's related information into DynamoDB.
        """
        try:
            with open(data_file, 'rb') as f:
                self.s3.upload_fileobj(f, self.s3_bucket, self.s3_file)
        except ClientError as e:
            self.logger.error('Couldn\'t upload the json file to s3: %s', e)
        else:
            self.dynamodb.insert_file_in_catalog(
                self.s3_file,
                f'{self.s3_bucket}/{self.s3_file}',
            )
