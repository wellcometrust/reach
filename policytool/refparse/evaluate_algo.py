"""
e.g. python test_algo.py --verbose True
"""

from argparse import ArgumentParser
import os
from os import listdir 
from datetime import datetime
from urllib.parse import urlparse

from utils import FileManager
from algo_evaluation.evaluate_settings import settings
from algo_evaluation.evaluate_find_section import evaluate_find_section
from algo_evaluation.evaluate_split_section import evaluate_split_section
from algo_evaluation.evaluate_parse import evaluate_parse
from algo_evaluation.evaluate_match_references import evaluate_match_references


def get_text(filename, foldername):

    try:
        references_section = open(
            "{}/{}.txt".format(foldername, filename)
        ).read()
    except:
        references_section = ""

    return references_section

def get_pdf_sections(
        pdf_name, sections_folder_names, sections_location
        ):
    """
    For a pdf name in the evaluation data, 
    get all the text from any relevant txt files in the locations given
    
    Input:
    pdf_name : A pdf name in the evaluation data 
                e.g pdf_name1
    sections_folder_names : 
                A list of the folder names for each
                section we have evaluation data for
                e.g. ['reference', 'bibliograph']
    sections_location : 
                The file location where each of the
                section folders are kept
                e.g './algo_evaluation/data_evaluate/pdf_sections'

    Output:
    sections_dict : 
                A dictionary of all the sections text
                for this pdf,
                in form {reference : 'text', bibliograph : 'text', ... }
    """
    sections = {}
    for section_folder in sections_folder_names:
        section_text = get_text(
            pdf_name,
            '{}/{}'.format(
                sections_location,
                section_folder
                )
            )
        sections.update({section_folder : section_text})
    
    return sections

def create_argparser():
    parser = ArgumentParser()
    parser.add_argument(
        '--verbose',
        help='Whether you want to print detailed test \
            information ("True") or not ("False")',
        default = True
    )

    return parser

if __name__ == '__main__':

    parser = create_argparser()
    args = parser.parse_args()

    now = datetime.now()
    logger = settings.logger
    logger.setLevel('INFO')

    logger.info('Starting tests...')

    log_file = open(
        '{}/Test results - {:%Y-%m-%d-%H%M}'.format(
            settings.LOG_FILE_PREFIX, now
        ), 'w'
    )
        
    log_file.write(
        'Date of test = {:%Y-%m-%d-%H%M}\n'.format(now)
    )

    logger.info('Reading files...')
    fm = FileManager()

    # ==== Load data to test scraping for tests 1 and 2: ====
    logger.info('[+] Reading {}'.format(
        settings.SCRAPE_DATA_PDF_FOLDER_NAME
        )
    )

    scrape_pdf_location = '{}/{}'.format(
        settings.FOLDER_PREFIX,
        settings.SCRAPE_DATA_PDF_FOLDER_NAME
    )

    pdf_names = listdir(scrape_pdf_location)
    pdf_names = [
        os.path.splitext(pdf_name)[0] for pdf_name in pdf_names
    ]
    pdf_names.remove('.DS_Store')

    sections_location = '{}/{}'.format(
        settings.FOLDER_PREFIX,
        settings.SCRAPE_DATA_REF_PDF_FOLDER_NAME
    )

    sections_folder_names = [
        name for name in os.listdir(sections_location) \
        if os.path.isdir('{}/{}'.format(sections_location, name))
    ]

    evaluate_find_section_data = {
        pdf_name : get_pdf_sections(
            pdf_name, sections_folder_names, sections_location
        ) for pdf_name in pdf_names
    }

    # ==== Load data to test split sections for test 3: ====
    logger.info('[+] Reading {}'.format(settings.NUM_REFS_FILE_NAME))
    evaluate_split_section_data = fm.get_file(
        settings.NUM_REFS_FILE_NAME,
        settings.FOLDER_PREFIX,
        'csv'
    )

    evaluate_split_section_data['Reference section'] = [
        get_text(
            doc_hash,
            '{}/{}'.format(
                settings.FOLDER_PREFIX,
                settings.NUM_REFS_TEXT_FOLDER_NAME
                )
            ) for doc_hash in evaluate_split_section_data['hash']
        ]

    # ==== Load data to test parse for test 4: ====
    logger.info('[+] Reading {}'.format(settings.PARSE_REFERENCE_FILE_NAME))
    evaluate_parse_data = fm.get_file(
        settings.PARSE_REFERENCE_FILE_NAME,
        settings.FOLDER_PREFIX,
        'csv'
    )

    # ==== Load data to test matching for test 5: ====
    logger.info('[+] Reading {}'.format(settings.TEST_PUB_DATA_FILE_NAME))
    evaluation_references = fm.get_file(
        settings.TEST_PUB_DATA_FILE_NAME,
        settings.FOLDER_PREFIX,
        'csv'
    )

    # Load WT publications to match references against
    logger.info('[+] Reading {}'.format(settings.MATCH_PUB_DATA_FILE_NAME))
    publications = fm.get_file(
        settings.MATCH_PUB_DATA_FILE_NAME,
        settings.FOLDER_PREFIX,
        'csv'
    )

    # Load the latest parser model
    model = fm.get_file(
        'reference_parser_pipeline.pkl',
        './reference_parser_models/',
        'pickle'
    )

    # ==== Get the evaluation metrics ====
    logger.info('\nStarting the tests...\n')

    logger.info('[+] Running tests 1 and 2')                     

    test1_scores, test2_scores = evaluate_find_section(
        evaluate_find_section_data,
        scrape_pdf_location,
        settings.LEVENSHTEIN_DIST_SCRAPER_THRESHOLD
    )

    logger.info('[+] Running test 3')
    test3_scores = evaluate_split_section(
        evaluate_split_section_data,
        settings.ORGANISATION_REGEX,
        settings.SPLIT_SECTION_SIMILARITY_THRESHOLD
        )

    logger.info('[+] Running test 4')

    test4_scores = evaluate_parse(parse_test_data, model, settings.LEVENSHTEIN_DIST_THRESHOLD)

    logger.info('[+] Running test 5')
    test5_scores = evaluate_match_references(publications, evaluation_references, settings.FUZZYMATCH_THRESHOLD)

    test_scores_list = [test1_scores, test2_scores, test3_scores, test4_scores, test5_scores]

    if args.verbose:
        for i, tests in enumerate(test_scores_list):
            log_file.write(
                "\n-----Information about test {}:-----\n".format(i)
            )
            [
                log_file.write(
                    "\n"+k+"\n"+str(v)+"\n"
                ) for (k,v) in tests.items()
            ]
    else:
        for i, tests in enumerate(test_scores_list):
            log_file.write("\nScore for test {}:\n".format(i))
            log_file.write(str(tests['Score']))

    log_file.close()

