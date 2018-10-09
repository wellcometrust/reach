import pandas as pd
import os
import pickle
from .s3 import S3
from io import StringIO
from settings import settings


def get_file(file_prefix, file_name):
    """Takes the path and name of a file and returns its content, from s3
    on production and from a local storage if debug mode is True.
    """
    if not settings.DEBUG or not file_name:
        s3 = S3(settings.BUCKET)

        # If we don't have the filename, take the last file
        if not file_name:
            file_path = s3._get_last_modified_file_key(file_prefix)
        else:
            file_path = os.path.join(file_prefix, file_name)
        file_content = s3.get(file_path)
    else:
        file_path = os.path.join(file_prefix, file_name)
        file_content = open(file_path, 'r').read()
    return file_content


def load_csv_file(file_prefix, file_name):
    """Takes the path and name of a csv file and returns its content.
    The file is loaded from S3 in production and from a local/cloud folder
    in dev mode.
    """
    file_content = get_file(file_prefix, file_name)
    csv_file = StringIO(file_content)
    raw_text_data = pd.read_csv(csv_file)
    return raw_text_data


def load_json_file(file_path, file_name):
    """Takes the path and name of a json file and returns its content.
    The file is loaded from S3 in production and from a local/cloud folder
    in dev mode.
    """
    file_content = get_file(file_path, file_name)
    raw_text_data = pd.read_json(file_content, lines=True)
    return raw_text_data


def load_pickle_file(file_dir, file_name):
    """Load a pickle file from a given path and file name and returns the
    unpickled file.
    """
    if not settings.DEBUG or not file_name:
        s3 = S3(settings.BUCKET)

        # If we don't have the filename, take the last file
        if not file_name:
            file_path = s3._get_last_modified_file_key(file_dir)
        else:
            file_path = os.path.join(file_dir, file_name)
        file_content = s3.get(file_path)
    else:
        file_path = os.path.join(file_dir, file_name)
        file_content = open(file_path, 'rb').read()
    unpickled_file = pickle.loads(file_content)
    return unpickled_file
