import pandas as pd
import os
import pickle
from .s3 import S3
from io import StringIO
from settings import settings


class FileManager():
    def __init__(self, mode='LOCAL'):
        self.mode = mode

        if self.mode == 'S3':
            self.s3 = S3(settings.BUCKET)

        self.loaders = {
            'csv': self.load_csv_file,
            'json': self.load_json_file,
            'pickle': self.load_pickle_file,
        }

    def get_file(self, file_name, file_prefix, file_type):
        if self.mode == 'S3':
            return self.get_from_s3(file_prefix, file_name, file_type)

        return self.get_from_local(file_prefix, file_name, file_type)

    def get_from_s3(self, file_prefix, file_name, file_type):
        # If we don't have the filename, take the last file
        if not file_name:
            file_path = self.s3._get_last_modified_file_key(file_prefix)
        else:
            file_path = os.path.join(file_prefix, file_name)
        file_content = self.s3.get(file_path)

        return self.loaders[file_type](file_content)

    def get_from_local(self, file_prefix, file_name, file_type):
        file_path = os.path.join(file_prefix, file_name)
        file_mode = 'rb' if type == 'pickle' else 'r'
        file_content = open(file_path, file_mode, encoding='utf-8').read()

        return self.loaders[file_type](file_content)

    def load_csv_file(self, file_content):
        """Takes the path and name of a csv file and returns its content."""
        csv_file = StringIO(file_content.decode('utf-8'))
        raw_text_data = pd.read_csv(csv_file)
        return raw_text_data

    def load_json_file(self, file_content):
        """Takes the path and name of a json file and returns its content."""
        raw_text_data = pd.read_json(file_content, lines=True)
        return raw_text_data

    def load_pickle_file(self, file_content):
        """Load a pickle file from a given path and file name and returns the
        unpickled file.
        """
        unpickled_file = pickle.loads(file_content)
        return unpickled_file
