import boto3
import logging
from datetime import datetime
from botocore.exceptions import ClientError


class DynamoDBConnector:
    """Connector to make the web scraper compatible with AWS Dynamodb. It relies
    on boto3 and uses the credentials stored in ~/.aws/credentials.
    """

    def __init__(self):
        """Initialise the connection, and create a logger instance."""
        self.logger = logging.getLogger(__name__)
        self.dynamodb = boto3.resource(
            'dynamodb',
            region_name='eu-west-2',
            endpoint_url='http://localhost:8765'
        )
        try:
            if 'scraper_articles' not in self.dynamodb.tables.all():
                self.logger.error('Article table does not exists.')
        except ClientError as e:
            self.logger.error(
                'Error when initialising the connection [%s]', e
            )

    def insert_article(self, file_hash, url):
        """Try to insert an article and its url in the article table. Return
        dynamodb response or `None` if the request fail.
        """
        try:
            table = self.dynamodb.Table("scraper_articles")
            response = table.put_item(Item={
                'file_hash': file_hash,
                'url': url
            })
        except ClientError as e:
            self.logger.error('Couldn\'t insert article [%s]', e)
            return

        return response

    def insert_file_in_catalog(self, file_index, file_path):
        """Insert the newly created file informations into the catalog table.
        """
        try:
            table = self.dynamodb.Table('scraper_catalog')
            response = table.put_item(Item={
                'file_index': file_index,
                'file_path': file_path,
                'date_created': datetime.now()
            })
        except ClientError as e:
            self.logger.error('Couldn\'t insert file in the catalog [%s]', e)
            return
        return response

    def is_scraped(self, file_hash):
        """Check wether or not a document has already been scraped by looking
        for its file hash into the article table."""
        try:
            table = self.dynamodb.Table('scraper_articles')
            item = table.get_item(
                TableName='scraper_articles',
                Key={
                    'file_hash': file_hash,
                },
                ConsistentRead=True,
            )
        except ClientError as e:
            self.logger.error('Couldn\'t fetch article [%s]', e)
            return False
        return 'Item' in item.keys()
