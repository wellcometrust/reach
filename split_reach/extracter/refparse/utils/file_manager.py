import pandas as pd
import gzip
import logging
import os
import pickle
import tempfile
import json

from .s3 import S3
from reach.refparse.settings import settings


class FileManager():
    def __init__(self, mode='LOCAL', bucket=settings.BUCKET):
        self.mode = mode
        self.logger = settings.logger
        self.logger.setLevel(logging.INFO)
        if self.mode == 'S3':
            self.s3 = S3(bucket)

        self.loaders = {
            'csv': self.load_csv_file,
            'json': self.load_json_file,
            'pickle': self.load_pickle_file,
        }

    def to_row(self, line, lineno, scraping_columns):
        try:
            return {
                k: v for k, v in json.loads(line).items()
                if k in scraping_columns
            }
        except Exception as e:
            self.logger.error(
                'Error on line %d: exception=%s line=%r',
                lineno, e, line)
            raise

    def get_scraping_results(
            self, file_name, file_prefix,
            scraping_columns=('title', 'file_hash', 'sections', 'uri', 'metadata')
            ):
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
                if file_name.endswith('.gz'):
                    with gzip.GzipFile(fileobj=tf, mode='r') as text_tf:
                        rows = (
                            self.to_row(line, lineno, scraping_columns)
                            for lineno, line in enumerate(text_tf)
                        )
                        return pd.DataFrame(rows)
                else:
                    rows = (
                        self.to_row(
                            line, lineno, scraping_columns
                            ) for lineno, line in enumerate(tf)
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
        if file_name.endswith('.gz'):
            with gzip.GzipFile(fileobj=tf) as text_tf:
                return self.loaders[file_type](text_tf)
        else:
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
