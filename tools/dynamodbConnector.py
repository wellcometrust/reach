import boto3
import logging
from datetime import datetime
from botocore.exceptions import ClientError


class DynamoDBConnector:
    """Connector to make the web scraper compatible with AWS Dynamodb. It relies
    on boto3 and uses the credentials stored in ~/.aws/credentials.
    """

    def __init__(self, region=''):
        """Initialise the connection, and create a logger instance."""
        self.logger = logging.getLogger(__name__)
        if region:
            self.dynamodb = boto3.client(
                'dynamodb',
                region_name=region
            )
        else:
            self.dynamodb = boto3.client('dynamodb')

    def insert_article(self, file_hash, url):
        """Try to insert an article and its url in the article table. Return
        dynamodb response or `None` if the request fail.
        """
        try:
            return self.dynamodb.put_item(
                TableName='scraper_articles',
                Item={
                    'file_hash': {'S': file_hash},
                    'url': {'S': url}
                }
            )
        except ClientError as e:
            self.logger.error('Couldn\'t insert article [%s]', e)
        except self.dynamodb.exceptions.ResourceNotFoundException:
            self.logger.error('Couldn\'t find the table scraper_articles')

    def insert_file_in_catalog(self, file_index, file_path):
        """Insert the newly created file informations into the catalog table.
        """
        try:
            return self.dynamodb.put_item(
                TableName='scraper_catalog',
                Item={
                    'file_index': {'S': file_index},
                    'file_path': {'S': file_path},
                    'date_created': {'S': str(datetime.now())}
                }
            )
        except ClientError as e:
            self.logger.error('Couldn\'t insert file in the catalog [%s]', e)
        except self.dynamodb.exceptions.ResourceNotFoundException:
            self.logger.error('Couldn\'t find the table scraper_catalog')

    def is_scraped(self, file_hash):
        """Check wether or not a document has already been scraped by looking
        for its file hash into the article table."""
        try:
            item = self.dynamodb.get_item(
                TableName='scraper_articles',
                Key={
                    'file_hash': {'S': file_hash},
                },
                ConsistentRead=True,
            )
            return 'Item' in item.keys()
        except ClientError as e:
            self.logger.error('Couldn\'t fetch article [%s]', e)
            return False
        except self.dynamodb.exceptions.ResourceNotFoundException:
            self.logger.error('Couldn\'t find the table scraper_articles')
