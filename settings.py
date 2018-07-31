import os


class BaseSettings:
    prediction_probability_threshold = 0.75
    blocksize = 1000
    fuzzymatch_threshold = 0.8

    organisation = os.environ.get('ORGANISATION', 'nice')

    BUCKET = "datalabs-data"
    raw_text_prefix = "scraper-results/{}".format(organisation)
    raw_text_file_name = None
    wt_references_prefix = "wellcome_publications"
    wt_references_file_name = None
    model_prefix = "reference_parser_models"
    classifier_file_name = "RefSorter_classifier.pkl"
    vectorizer_file_name = file_name = "RefSorter_vectorizer.pkl"

    regex_dict = {
        'who_iris': "(|\.)\\n[0-9]{1,3}\.(\s|\\n)",
        'nice': "\n",
        'unicef': "\\n[0-9]{1,3}(\.|)\s{0,2}(\\n|)",
        'msf': "\\n[0-9]{0,3}(\.\s{0,2}|\\n)"
    }
    organisation_regex = regex_dict.get(organisation, "\n")


class ProdSettings(BaseSettings):
    DEBUG = False

    RDS_USERNAME = os.environ.get('RDS_USERNAME')
    RDS_PASSWORD = os.environ.get('RDS_PASSWORD')
    RDS_HOST = os.environ.get('RDS_HOST')
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
    'PROD': ProdSettings
}
settings = settings_mode[os.environ.get('REF_PARSER_SETTINGS', 'DEV')]
