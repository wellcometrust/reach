import os
from settings import BaseSettings


class TestSettings(BaseSettings):
    DEBUG = True

    FOLDER_PREFIX = "./algo_tests/data_test"
    LOG_FILE_PREFIX = './algo_tests/results'

    SCRAPE_DATA_FILE_NAME = "scrape_test_data.csv"

    NUM_REFS_FILE_NAME = "split_section_test_data.csv"
    NUM_REFS_TEXT_FOLDER_NAME = "scraped_references_sections"

    PARSE_REFERENCE_FILE_NAME = "actual_reference_structures_sample.csv"

    TEST_PUB_DATA_FILE_NAME = "positive_and_negative_match_test_data.csv"

    MATCH_PUB_DATA_FILE_NAME = "uber_api_publications.csv"

settings = TestSettings()
