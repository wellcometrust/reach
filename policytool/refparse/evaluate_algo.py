"""
e.g. python test_algo.py --verbose True
"""

from argparse import ArgumentParser
import os

from utils import FileManager
from datetime import datetime
from urllib.parse import urlparse

from algo_evaluation.evaluate_settings import settings
from algo_evaluation.evaluate_find_section import evaluate_find_section
from algo_evaluation.evaluate_split_section import evaluate_split_section
from algo_evaluation.evaluate_parse import evaluate_parse
from algo_evaluation.evaluate_match_references import evaluate_match_references


def get_references_sections(filenames, foldername):

    references_sections = []
    for filename in filenames:
        section = open("{}/{}.txt".format(foldername, filename)).read()
        references_sections.append(section)

    return references_sections

def create_argparser():
    parser = ArgumentParser()
    parser.add_argument(
        '--verbose',
        help='Whether you want to print detailed test information ("True") or not ("False")',
        default = False
    )

    return parser

if __name__ == '__main__':

    parser = create_argparser()
    args = parser.parse_args()

    verbose='FALSE'

    now = datetime.now()
    logger = settings.logger
    logger.setLevel('INFO')

    logger.info('Starting tests...')

    log_file = open(
        '{}/Test results - {:%Y-%m-%d-%H%M}'.format(settings.LOG_FILE_PREFIX, now), 'w'
        )
        
    log_file.write(
        'Date of test = {:%Y-%m-%d-%H%M}\n'.format(now)
        )

    logger.info('Reading files...')
    fm = FileManager()

    # Load data to test scraping for tests 1 and 2:
    logger.info('[+] Reading {}'.format(settings.SCRAPE_DATA_FILE_NAME))
    scrape_test_data = fm.get_file(
        settings.SCRAPE_DATA_FILE_NAME,
        settings.FOLDER_PREFIX,
        'csv'
    )

    # Load data to test split sections for test 3:
    logger.info('[+] Reading {}'.format(settings.NUM_REFS_FILE_NAME))
    split_section_test_data = fm.get_file(
        settings.NUM_REFS_FILE_NAME,
        settings.FOLDER_PREFIX,
        'csv'
    )
    references_sections = get_references_sections(
                            split_section_test_data['hash'],
                            '{}/{}'.format(
                                settings.FOLDER_PREFIX,
                                settings.NUM_REFS_TEXT_FOLDER_NAME
                                )
                            )
    split_section_test_data['Reference section'] = references_sections

    # Load data to test parse for test 4:
    logger.info('[+] Reading {}'.format(settings.PARSE_REFERENCE_FILE_NAME))
    parse_test_data = fm.get_file(
        settings.PARSE_REFERENCE_FILE_NAME,
        settings.FOLDER_PREFIX,
        'csv'
    )

    # Load data to test matching for test 5:
    logger.info('[+] Reading {}'.format(settings.TEST_PUB_DATA_FILE_NAME))
    test_publications = fm.get_file(
        settings.TEST_PUB_DATA_FILE_NAME,
        settings.FOLDER_PREFIX,
        'csv'
    )

    # Load WT publications to match references against
    logger.info('[+] Reading {}'.format(settings.MATCH_PUB_DATA_FILE_NAME))
    match_publications = fm.get_file(
        settings.MATCH_PUB_DATA_FILE_NAME,
        settings.FOLDER_PREFIX,
        'csv'
    )

    # Load the latest parser model
    model = fm.get_file('reference_parser_pipeline.pkl','./reference_parser_models/','pickle')

    logger.info('\nStarting the tests...\n')

    logger.info('[+] Running tests 1 and 2')
    test1_scores, test2_scores = evaluate_find_section(scrape_test_data)

    logger.info('[+] Running test 3')
    test3_scores = evaluate_split_section(
        split_section_test_data,
        settings.ORGANISATION_REGEX,
        settings.SPLIT_SECTION_SIMILARITY_THRESHOLD
        )

    logger.info('[+] Running test 4')
    test4_scores = evaluate_parse(parse_test_data, model, settings.LEVENSHTEIN_DIST_THRESHOLD)

    logger.info('[+] Running test 5')
    test5_scores = evaluate_match_references(match_publications, test_publications, settings.FUZZYMATCH_THRESHOLD)

    test_scores_list = [test1_scores, test2_scores, test3_scores, test4_scores, test5_scores]
    if args.verbose == 'True':
        for i, tests in enumerate(test_scores_list):
            log_file.write("\nInformation about test {}:\n".format(i))
            log_file.write(tests)
    else:
        for i, tests in enumerate(test_scores_list):
            log_file.write("\nScore for test {}:\n".format(i))
            log_file.write(str(tests['Score']))

    log_file.close()

