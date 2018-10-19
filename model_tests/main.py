from utils import load_csv_file
from datetime import datetime
from .test_settings import settings
from . import (test_model_predictions, test_reference_number,
               test_reference_structuring, test_fuzzy_matching)


def run_tests():
    now = datetime.now()
    logger = settings.logger
    logger.setLevel('INFO')

    organisations = settings.ORGANISATIONS

    logger.info('Starting tests...')

    log_file = open(
        f'{settings.LOG_FILE_PREFIX}/Test results - ' + str(now), 'w')
    log_file.write(
        'Organisations = ' + str(settings.ORGANISATIONS) + '\n' +
        'Regexes used = ' + repr(settings._regex_dict) + '\n' +
        'Date of test = ' + str(now) + '\n' +
        'Number of publications in test set = ' +
        str(settings.TEST_SET_SIZE) + '\n' +
        'WT publication data file name = ' +
        str(settings.PUB_DATA_FILE_NAME) + '\n\n'
    )

    logger.info('Reading files...')

    logger.info(f'[+] Reading {settings.PUB_DATA_FILE_NAME}')
    # Load publication data for testing model predictions
    publications = load_csv_file(
        settings.FOLDER_PREFIX,
        settings.PUB_DATA_FILE_NAME
    )

    logger.info(f'[+] Reading {settings.NUM_REFS_FILE_NAME}')
    # Load manually found number of references for a sample of documents
    actual_number_refs = load_csv_file(
        settings.FOLDER_PREFIX,
        settings.NUM_REFS_FILE_NAME
    )

    logger.info(f'[+] Reading {settings.STRUCT_REFS_FILE_NAME}')
    # Load manually found structure of references for a sample of documents
    actual_reference_structures = load_csv_file(
        settings.FOLDER_PREFIX,
        settings.STRUCT_REFS_FILE_NAME
    )

    logger.info(f'[+] Reading {settings.MATCH_PUB_DATA_FILE_NAME}')
    # Load WT publications to match references against
    match_publications = load_csv_file(
        settings.FOLDER_PREFIX,
        settings.MATCH_PUB_DATA_FILE_NAME
    )

    logger.info(f'[+] Reading {settings.TEST_PUB_DATA_FILE_NAME}')
    test_publications = load_csv_file(
        settings.FOLDER_PREFIX,
        settings.TEST_PUB_DATA_FILE_NAME
    )

    logger.info('Starting the tests...')
    logger.info('[+] Running test 1')
    test1_info, test1_score = test_model_predictions(publications)

    logger.info('[+] Running test 2')
    test2_infos, test2_score = test_reference_number(actual_number_refs)

    logger.info('[+] Running test 3')
    test3_infos, test3_score = test_reference_structuring(
        actual_reference_structures
    )

    logger.info('[+] Running test 4')
    test4_info, test4_score = test_fuzzy_matching(
        match_publications,
        test_publications
    )

    log_file.write('=====\nTest 1:\n=====\n' + test1_info)

    log_file.write('=====\nTest 2:\n=====\n')
    for org in organisations:
        log_file.write(f'{org} --- {test2_infos.get(org)}')

    log_file.write('=====\nTest 3:\n=====\n')
    for org in organisations:
        log_file.write(f'{org} --- {test3_infos.get(org)}')

    log_file.write('=====\nTest 4:\n=====\n' + test4_info)

    # Summary
    # ========================================
    logger.info("============")
    logger.info("Summary")
    logger.info("===========")

    logger.info(test1_score)
    logger.info(test2_score)
    logger.info(test2_score['who_iris'])
    logger.info(test3_score['who_iris'])
    logger.info(test4_score)

    overall_scores = []
    for org in organisations:
        if not test2_score.get(org) or not test3_score.get(org):
            continue
        overall_scores.append({
            org:
                test1_score
                * test2_score.get(org)
                * test3_score.get(org)
                * test4_score
        })

    summary_info = str(
        "Test 1 = " + str(test1_score) + '\n' +
        "Test 2 = " + str(test2_score) + '\n' +
        "Test 3 = " + str(test3_score) + '\n' +
        "Test 4 = " + str(test4_score) + '\n' +
        "Overall score = " + str(overall_scores))
    print(summary_info)

    log_file.write("=====\nSummary:\n=====\n" + summary_info)

    log_file.close()


if __name__ == '__main__':
    run_tests()
