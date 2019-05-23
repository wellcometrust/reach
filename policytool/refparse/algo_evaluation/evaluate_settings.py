import os
from settings import BaseSettings

class TestSettings(BaseSettings):

    SPLIT_SECTION_SIMILARITY_THRESHOLD = 40

    LEVENSHTEIN_DIST_THRESHOLD = 0.3
    LEVENSHTEIN_DIST_SCRAPER_THRESHOLD = 0.3

    FOLDER_PREFIX = "./algo_evaluation/data_evaluate"
    LOG_FILE_PREFIX = './algo_evaluation/results'

    SCRAPE_DATA_PDF_FOLDER_NAME = "pdfs"
    SCRAPE_DATA_REF_PDF_FOLDER_NAME = "pdf_sections"

    NUM_REFS_FILE_NAME = "split_section_test_data.csv"
    NUM_REFS_TEXT_FOLDER_NAME = "scraped_references_sections"

    MODEL_FILE_TYPE = 'pickle'
    MODEL_FILE_PREFIX = './reference_parser_models/'
    MODEL_FILE_NAME = 'reference_parser_pipeline.pkl'
    PARSE_REFERENCE_FILE_NAME = "actual_reference_structures_sample.csv"

    TEST_PUB_DATA_FILE_NAME = "positive_and_negative_match_test_data.csv"

    MATCH_PUB_DATA_FILE_NAME = "uber_api_publications.csv"

settings = TestSettings()
