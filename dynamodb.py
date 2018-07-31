import logging

import boto3

from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class DynamoDb():
    def __init__(self):
        self.dynamodb = boto3.client(
                'dynamodb',
                region_name='eu-west-1'
        )

    def _remove_empty_values(self, serialised_item):
        return {
            key: value
            for key, value in serialised_item.items()
            if value['S']
        }

    def put(self, table_name, table_item):
        try:
            self.dynamodb.put_item(
                TableName=table_name,
                Item=self._remove_empty_values(table_item)
            )
        except ClientError as e:
            logger.error(
                'Couldn\'t insert item in table {}'.format(table_name),
                str(e)
            )
        except self.dynamodb.exceptions.ResourceNotFoundException:
            logger.error('Couldn\'t find the table {}'.format(table_name))
