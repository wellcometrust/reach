import os
from settings import BaseSettings


class TestSettings(BaseSettings):
    DEBUG = True

    RDS_USERNAME = 'postgres'
    RDS_PASSWORD = ''
    RDS_HOST = '127.0.0.1'
    RDS_PORT = os.environ.get('RDS_PORT', 5437)
    RDS_REFERENCES_DATABASE = "parser_references_test"

    RDS_URL = "postgresql+psycopg2://{user}:{passw}@{host}:{port}/{db}".format(
          user=RDS_USERNAME,
          passw=RDS_PASSWORD,
          host=RDS_HOST,
          port=RDS_PORT,
          db=RDS_REFERENCES_DATABASE
    )
    FOLDER_PREFIX = "./model_tests/data_test"
    LOG_FILE_PREFIX = './model_tests/results'

    PUB_DATA_FILE_NAME = ''.join([
        "Publication Year is 2017 ",
        "Funder is WT ",
        "Dimensions-Publication-2018-02-13_11-23-53",
        ".csv",
    ])

    TEST_PUB_DATA_FILE_NAME = "positive_and_negative_publication_samples.csv"

    MATCH_PUB_DATA_FILE_NAME = "uber_api_publications.csv"

    NUM_REFS_FILE_NAME = "actual_number_refs_sample.csv"
    NUM_REFS_TITLE_NAME = "Number of References in pdf"

    STRUCT_REFS_FILE_NAME = "actual_reference_structures_sample.csv"

    TEST_SET_SIZE = 100  # Number of publications to use to test model
    PREDICTION_PROBABILITY_THRESHOLD = 0.75
    TEST2_THRESH = 0.4
    FUZZYMATCH_SAMPLE = 200

    ORGANISATIONS = ['who_iris', 'nice', 'unicef', 'msf']

    # Unstructured references from latest policy scrape:

    RAW_PUBLICATION_ID_NAME = "hash"
    ACTUAL_PUBLICATION_ID_NAME = "hash"
    COMPONENTS_ID_NAME = "Document id"
    ACTUAL_UBER_ID_NAME = "uber_uber_id"


settings = TestSettings()
