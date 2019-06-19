import os
from settings import BaseSettings

class TestSettings(BaseSettings):

    FOLDER_PREFIX = "./algo_evaluation/data_evaluate"
    LOG_FILE_PREFIX = './algo_evaluation/results'

    # Variables for find section evaluation data
    LEVENSHTEIN_DIST_SCRAPER_THRESHOLD = 0.3
    SCRAPE_DATA_PDF_FOLDER_NAME = "pdfs"
    SCRAPE_DATA_REF_PDF_FOLDER_NAME = "pdf_sections"

    # Variables for split section evaluation data
    SPLIT_SECTION_SIMILARITY_THRESHOLD = 40
    NUM_REFS_FILE_NAME = "split_section_test_data.csv"
    NUM_REFS_TEXT_FOLDER_NAME = "scraped_references_sections"

    # Variables for parse evaluation data
    LEVENSHTEIN_DIST_PARSE_THRESHOLD = 0.3
    MODEL_FILE_TYPE = 'pickle'
    MODEL_FILE_PREFIX = './reference_parser_models/'
    MODEL_FILE_NAME = 'reference_parser_pipeline.pkl'
    PARSE_REFERENCE_FILE_NAME = "actual_reference_structures_sample.csv"

    # Variables for match evaluation data
    EVAL_PUB_DATA_FILE_NAME = "epmc-metadata.json"
    EVAL_MATCH_NUMBER = 100000
    EVAL_SAMPLE_MATCH_NUMBER = 10000
    LENGTH_THRESHOLD = 50
    MATCH_THRESHOLD = 0.8

settings = TestSettings()
