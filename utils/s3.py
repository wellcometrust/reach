import boto3
from settings import settings
from botocore.exceptions import ClientError


class S3():
    def __init__(self, bucket_name):
        self.logger = settings.logger
        self.s3 = boto3.resource('s3')
        self.client = boto3.client('s3')
        self.bucket_name = bucket_name

    def _get_last_modified_file_key(self, prefix):
        try:
            objs = self.client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            ).get('Contents', [])
        except ClientError:
            print('Could not connect to s3 bucket.')
            return ''

        if not objs:
            print('Could not get last result file.')
            last_added = []
            return last_added
        else:
            last_added = [
                obj['Key']
                for obj in sorted(
                    objs,
                    key=lambda obj: obj['LastModified'],
                    reverse=True)
            ][0]
            return last_added

    def get(self, key):
        self.logger.info('[+] Trying to fetch %s from s3', key)
        last_file = self.client.get_object(
            Bucket=self.bucket_name,
            Key=key,
        )
        last_content = last_file.get('Body').read()

        return last_content
