import os
import logging

logging.basicConfig(format='[%(asctime)s]:%(levelname)s - %(message)s')


class BaseSettings:
    logger = logging.getLogger(__name__)

    DEBUG = True

    PREDICTION_PROBABILITY_THRESHOLD = 0.75
    FUZZYMATCH_THRESHOLD = 0.8

    ORGANISATION = os.environ.get('ORGANISATION', 'nice')

    BUCKET = "datalabs-data"

    SCRAPER_RESULTS_BASEDIR = "s3://{}/scraper-results".format(BUCKET)
    SCRAPER_RESULTS_DIR = "{}/{}".format(SCRAPER_RESULTS_BASEDIR, ORGANISATION)
    SCRAPER_RESULTS_FILENAME = ''

    REFERENCES_DIR = "s3://{}/wellcome_publications".format(BUCKET)
    REFERENCES_FILENAME = 'uber_api_publications.csv'

    LOCAL_OUTPUT_DIR = 'local_output'
    PREF_REFS_FILENAME = 'predicted_reference_structures.csv'
    MATCHES_FILENAME = 'all_match_data.csv'

    MODEL_DIR = "s3://{}/reference_parser_models".format(BUCKET)
    CLASSIFIER_FILENAME = "RefSorter_classifier.pkl"
    VECTORIZER_FILENAME = "RefSorter_vectorizer.pkl"

    _regex_dict = {
        'who_iris': "(|\.)\\n[0-9]{1,3}\.(\s|\\n)",
        'nice': "(|\s)(|.)(|\s)\n(|[0-9]{1,3})(|.)(|\s)(?=[A-Z])",
        'unicef': "\\n[0-9]{1,3}(\.|)\s{0,2}(\\n|)",
        'msf': "\\n[0-9]{0,3}(\.\s{0,2}|\\n)"
    }
    ORGANISATION_REGEX = _regex_dict.get(ORGANISATION, "\n")

    REF_CLASSES = ['Authors', 'Journal', 'Volume', 'Issue', 'Pagination', 'Title','PubYear']


class ProdSettings(BaseSettings):
    DEBUG = False

    RDS_USERNAME = os.environ.get('RDS_USERNAME')
    RDS_PASSWORD = os.environ.get('RDS_PASSWORD')
    RDS_HOST = os.environ.get('RDS_HOST')
    RDS_PORT = os.environ.get('RDS_PORT', 5432)
    RDS_REFERENCES_DATABASE = "parser_references"

    S3 = True

    OUTPUT_URL = "postgresql+psycopg2://{user}:{passw}@{host}:{port}/{db}".format(
          user=RDS_USERNAME,
          passw=RDS_PASSWORD,
          host=RDS_HOST,
          port=RDS_PORT,
          db=RDS_REFERENCES_DATABASE
    )
    RDS_URL = OUTPUT_URL  # DEPRECATED


class LocalSettings(BaseSettings):
    DEBUG = True

    S3 = False

    RDS_USERNAME = 'postgres'
    RDS_PASSWORD = ''
    RDS_HOST = '127.0.0.1'
    RDS_PORT = os.environ.get('RDS_PORT', 5432)
    RDS_REFERENCES_DATABASE = "parser_references"

    SCRAPER_RESULTS_DIR = "scraper-results/{}".format(
        BaseSettings.ORGANISATION
    )
    REFERENCES_DIR = "wellcome_publications"
    MODEL_DIR = "reference_parser_models"

    OUTPUT_URL = "postgresql+psycopg2://{user}:{passw}@{host}:{port}/{db}".format(
          user=RDS_USERNAME,
          passw=RDS_PASSWORD,
          host=RDS_HOST,
          port=RDS_PORT,
          db=RDS_REFERENCES_DATABASE
    )
    RDS_URL = OUTPUT_URL  # DEPRECATED


settings_mode = {
    'DEV': BaseSettings,
    'LOCAL': LocalSettings,
    'PROD': ProdSettings
}
settings = settings_mode[os.environ.get('REF_PARSER_SETTINGS', 'LOCAL')]
