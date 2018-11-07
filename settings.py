import os
import logging

logging.basicConfig(format='[%(asctime)s]:%(levelname)s - %(message)s')


class BaseSettings:
    logger = logging.getLogger(__name__)

    DEBUG = True

    PREDICTION_PROBABILITY_THRESHOLD = 0.75
    BLOCKSIZE = 1000
    FUZZYMATCH_THRESHOLD = 0.8

    ORGANISATION = os.environ.get('ORGANISATION', 'who_iris')

    BUCKET = "datalabs-data"

    SCRAPER_RESULTS_DIR = "scraper-results/{}".format(ORGANISATION)
    SCRAPER_RESULTS_FILENAME = 'who_iris.json'

    REFERENCES_DIR = "wellcome_publications"
    REFERENCES_FILENAME = 'uber_api_publications.csv'

    MODEL_DIR = "reference_parser_models"
    CLASSIFIER_FILENAME = "RefSorter_classifier.pkl"
    VECTORIZER_FILENAME = "RefSorter_vectorizer.pkl"

    _regex_dict = {
        'who_iris': "(|\.)\\n[0-9]{1,3}\.(\s|\\n)",
        'nice': "(|\s)(|.)(|\s)\n(|[0-9]{1,3})(|.)(|\s)(?=[A-Z])",
        'unicef': "\\n[0-9]{1,3}(\.|)\s{0,2}(\\n|)",
        'msf': "\\n[0-9]{0,3}(\.\s{0,2}|\\n)"
    }
    ORGANISATION_REGEX = _regex_dict.get(ORGANISATION, "\n")


class ProdSettings(BaseSettings):
    DEBUG = False

    RDS_USERNAME = os.environ.get('RDS_USERNAME')
    RDS_PASSWORD = os.environ.get('RDS_PASSWORD')
    RDS_HOST = os.environ.get('RDS_HOST')
    RDS_PORT = os.environ.get('RDS_PORT', 5432)
    RDS_REFERENCES_DATABASE = "parser_references"

    S3 = True

    RDS_URL = "postgresql+psycopg2://{user}:{passw}@{host}:{port}/{db}".format(
          user=RDS_USERNAME,
          passw=RDS_PASSWORD,
          host=RDS_HOST,
          port=RDS_PORT,
          db=RDS_REFERENCES_DATABASE
    )


class LocalSettings(BaseSettings):
    DEBUG = True

    S3 = True

    RDS_USERNAME = 'postgres'
    RDS_PASSWORD = ''
    RDS_HOST = '127.0.0.1'
    RDS_PORT = os.environ.get('RDS_PORT', 5432)
    RDS_REFERENCES_DATABASE = "parser_references"

    RDS_URL = "postgresql+psycopg2://{user}:{passw}@{host}:{port}/{db}".format(
          user=RDS_USERNAME,
          passw=RDS_PASSWORD,
          host=RDS_HOST,
          port=RDS_PORT,
          db=RDS_REFERENCES_DATABASE
    )


settings_mode = {
    'DEV': BaseSettings,
    'LOCAL': LocalSettings,
    'PROD': ProdSettings
}
settings = settings_mode[os.environ.get('REF_PARSER_SETTINGS', 'LOCAL')]
