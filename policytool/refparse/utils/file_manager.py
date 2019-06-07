import pandas as pd
import os
import pickle
import dill
import tempfile
import json
from .s3 import S3
from policytool.refparse.settings import settings

SCRAPING_COLUMNS = ('title', 'hash', 'sections', 'uri')


class FileManager():
    def __init__(self, mode='LOCAL', bucket=settings.BUCKET):
        self.mode = mode
        self.logger = settings.logger
        self.logger.setLevel('INFO')
        if self.mode == 'S3':
            self.s3 = S3(bucket)

        self.loaders = {
            'csv': self.load_csv_file,
            'json': self.load_json_file,
            'pickle': self.load_pickle_file,
            'dill': self.load_dill_file
        }

    def to_row(self, line, lineno):
        try:
            return {
                k: v for k, v in json.loads(line).items()
                if k in SCRAPING_COLUMNS
            }
        except Exception as e:
            self.logger.error("Error on line %d: %s", lineno, e)
            raise

    def get_scraping_results(self, file_name, file_prefix):
        """Takes a scraping result-json to return it cleared of its unused
        parts, as a pandas DataFrame. This function is used instead of the
        others because of the size of the scraper result files, which requires
        a tempfile and some field filtering.

            In: file_name: the name of the json file
                file_prefix: the path to the file (excluding the file name)

            Out: A pandas.DataFrame containing the json's interesting items
        """
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
                rows = (
                    self.to_row(line, lineno) for lineno, line in enumerate(tf)
                )
                return pd.DataFrame(rows)

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
        with open(file_path, 'rb') as file_content:
            self.logger.info('Using %s file from local storage', file_path)
            dataframe = self.loaders[file_type](file_content)

        return dataframe

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

    def load_dill_file(self, file_content):
        """Load a dill file from a given path and file name and returns the
        unpickled file.
        """
        loaded_dill_file = dill.load(file_content)
        return loaded_dill_file
