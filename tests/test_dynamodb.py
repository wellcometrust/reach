import unittest
import boto3
from moto import mock_dynamodb2
from tools import DynamoDBConnector


@mock_dynamodb2
class TestScraperArticles(unittest.TestCase):
    """Test dynamodb scraper_articles related methods from the
    DynamoDBConnector module.
    """
    def setUp(self):
        """Initialise the dynamodb connector and create a mock table."""
        self.dynamodb = DynamoDBConnector('us-east-1')
        client = boto3.client('dynamodb', region_name='us-east-1')
        client.create_table(
            AttributeDefinitions=[
                {
                    'AttributeName': 'file_hash',
                    'AttributeType': 'S'
                },
            ],
            TableName='scraper_articles',
            KeySchema=[
                {
                    'AttributeName': 'file_hash',
                    'KeyType': 'HASH'
                },
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 1,
                'WriteCapacityUnits': 1
            },
        )

    def test_insert_dynamo_article(self):
        """Check if the is_scraped and the insert_article methods are working
        properly.
        """
        self.assertFalse(self.dynamodb.is_scraped('00'))
        self.dynamodb.insert_article('0' * 32, 'http://foo.bar')
        self.assertTrue(self.dynamodb.is_scraped('0' * 32))


@mock_dynamodb2
class TestsScraperCatalog(unittest.TestCase):
    """Test dynamodb scraper_catalog related methods from the
    DynamoDBConnector module.
    """
    def setUp(self):
        """Initialise the dynamodb connector and create a mock table."""
        self.dynamodb = DynamoDBConnector('us-east-1')
        client = boto3.client('dynamodb', region_name='us-east-1')
        client.create_table(
            AttributeDefinitions=[
                {
                    'AttributeName': 'file_index',
                    'AttributeType': 'S'
                },
            ],
            TableName='scraper_catalog',
            KeySchema=[
                {
                    'AttributeName': 'file_index',
                    'KeyType': 'HASH'
                },
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 1,
                'WriteCapacityUnits': 1
            },
        )

    def test_insert_file_in_catalog(self):
        """Check if the insert_file_in_catalog method is working."""
        client = boto3.client('dynamodb', region_name='us-east-1')
        item = client.get_item(
            TableName='scraper_catalog',
            Key={
                'file_index': {'S': 'foo'},
            },
            ConsistentRead=True,
        )
        self.assertFalse('Item' in item.keys())
        self.dynamodb.insert_file_in_catalog('index', '/foo/bar')
        item = client.get_item(
            TableName='scraper_catalog',
            Key={
                'file_index': {'S': 'index'},
            },
            ConsistentRead=True,
        )
