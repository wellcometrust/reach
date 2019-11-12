import os
import logging

class BaseSettings:
    logger = logging.getLogger(__name__)

    DEBUG = True

    PREDICTION_PROBABILITY_THRESHOLD = 0.75
    FUZZYMATCH_SIMILARITY_THRESHOLD = 0.8

    BUCKET = "datalabs-data"

    SCRAPER_RESULTS_BASEDIR = "s3://{}/scraper-results".format(BUCKET)
    SCRAPER_RESULTS_DIR = "{}".format(SCRAPER_RESULTS_BASEDIR)
    SCRAPER_RESULTS_FILENAME = ''

    LOCAL_OUTPUT_DIR = 'local_output'
    STRUCTURED_REFS_FILENAME = 'structured_references.json'
    MATCHED_REFS_FILENAME = 'matched_references.json'

    MODEL_DIR = "s3://{}/reference_parser_models".format(BUCKET)
    CLASSIFIER_FILENAME = "reference_parser_pipeline.pkl"

    MIN_CHAR_LIMIT = 20
    MATCH_TITLE_LENGTH_THRESHOLD = 40

    REF_CLASSES = ['Authors', 'Journal', 'Volume', 'Issue', 'Pagination', 'Title','PubYear']


class ProdSettings(BaseSettings):
    DEBUG = False
    S3 = True


class LocalSettings(BaseSettings):
    DEBUG = True
    S3 = False
    SCRAPER_RESULTS_DIR = "scraper-results"
    MODEL_DIR = "reference_parser_models"


settings_mode = {
    'DEV': BaseSettings,
    'LOCAL': LocalSettings,
    'PROD': ProdSettings
}
settings = settings_mode[os.environ.get('REF_PARSER_SETTINGS', 'LOCAL')]
