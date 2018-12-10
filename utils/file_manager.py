import pandas as pd
import os
import pickle
import tempfile
import jsonlines
from .s3 import S3
from settings import settings


class FileManager():
    def __init__(self, mode='LOCAL'):
        self.mode = mode
        self.logger = settings.logger
        self.logger.setLevel('INFO')
        if self.mode == 'S3':
            self.s3 = S3(settings.BUCKET)

        self.loaders = {
            'csv': self.load_csv_file,
            'json': self.load_json_file,
            'pickle': self.load_pickle_file,
        }

    def get_scraping_results(self, file_name, file_prefix):
        if self.mode == 'S3':
            with tempfile.TemporaryFile() as tf:
                # If we don't have the filename, take the last file
                if not file_name:
                    file_path = self.s3._get_last_modified_file_key(
                        file_prefix
                    )
                else:
                    file_path = os.path.join(file_prefix, file_name)
                self.s3.get(file_path, tf)
                tf.seek(0)
                self.logger.info('Using %s file from S3', file_path)
                columns_to_keep = [
                    "title",
                    "hash",
                    "sections",
                    "uri"
                ]
                json_file = []
                for obj in jsonlines.Reader(tf):
                    new_row = {}
                    for column in columns_to_keep:
                        new_row[column] = obj[column]
                    json_file.append(new_row)
            return pd.DataFrame(json_file)

        return self._get_from_local(file_prefix, file_name, 'json')

    def get_file(self, file_name, file_prefix, file_type):
        if self.mode == 'S3':
            with tempfile.TemporaryFile() as tf:
                return self._get_from_s3(file_prefix, file_name, file_type, tf)

        return self._get_from_local(file_prefix, file_name, file_type)

    def _get_from_s3(self, file_prefix, file_name, file_type, tf):
        # If we don't have the filename, take the last file
        if not file_name:
            file_path = self.s3._get_last_modified_file_key(file_prefix)
        else:
            file_path = os.path.join(file_prefix, file_name)
        self.s3.get(file_path, tf)
        tf.seek(0)
        self.logger.info('Using %s file from S3', file_path)
        return self.loaders[file_type](tf)

    def _get_from_local(self, file_prefix, file_name, file_type):
        file_path = os.path.join(file_prefix, file_name)
        file_content = open(file_path, 'rb').read()

        self.logger.info('Using %s file from local storage', file_path)
        return self.loaders[file_type](file_content)

    def load_csv_file(self, file_content):
        """Takes the path and name of a csv file and returns its content."""
        # csv_file = StringIO(file_content.decode('utf-8'))
        raw_text_data = pd.read_csv(file_content)
        return raw_text_data

    def load_json_file(self, temp_file):
        """Takes the path and name of a json file and returns its content."""
        raw_text_data = pd.read_json(temp_file, lines=True)
        return raw_text_data

    def load_pickle_file(self, file_content):
        """Load a pickle file from a given path and file name and returns the
        unpickled file.
        """
        unpickled_file = pickle.loads(file_content.read())
        return unpickled_file
