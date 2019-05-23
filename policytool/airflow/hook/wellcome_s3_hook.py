""" Extends airflow's S3Hook for checking file timestamps. """

from botocore.exceptions import ClientError

from airflow.hooks.S3_hook import S3Hook


class WellcomeS3Hook(S3Hook):

    def head_url(self, s3_url, **kwargs):
        """ Calls S3.Client.head_object() on a given S3 URL, including
        optional keyword arguments. """

        bucket_name, key = self.parse_s3_url(s3_url)
        return self.get_conn().head_object(
            Bucket=bucket_name, Key=key, **kwargs
        )


    def get_key_last_modified(self, s3_url):
        try:
            head = self.head_url(s3_url)
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return None
            raise
        return head['LastModified'] 


    def check_key_up_to_date(self, dst_s3_url, src_s3_urls):
        """ Returns true if dst_s3_url is newer than src_s3_urls. """

        try:
            dst_head = self.head_url(dst_s3_url)
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            raise

        dst_last_modified = dst_head['LastModified']
        for s3_url in src_s3_urls:
            last_modified = self.get_key_last_modified(s3_url)
            if last_modified is None:
                raise Exception("Source key is missing: %s" % s3_url)
            if last_modified > dst_last_modified:
                return False

        return True
