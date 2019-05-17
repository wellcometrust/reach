"""
e.g. python test_algo.py --verbose True
"""

from argparse import ArgumentParser
import os
from os import listdir 

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
        try:
            section = open("{}/{}.txt".format(foldername, filename)).read()
        except:
            section = ""
        references_sections.append(section)

    return references_sections

def get_sections_text_dict(pdf_names, sections_folder_names, sections_location):
    """
    For each pdf in the evaluation data, get all the text from each txt file in the location given
    
    Input:
    pdf_names : A list of the pdf names in the evaluation data 
                e.g [pdf_name1, pdf_name2, ...]
    sections_folder_names : 
                A list of the folder names for each section we have evaluation data for
                e.g. ['reference', 'bibliograph']
    sections_location : 
                The file location where each of the section folders are kept
                e.g './algo_evaluation/data_evaluate/pdf_sections'

    Output:
    sections_dict : 
                A nested dictionary of all the sections text for each pdf in the evaluation data,
                in form {pdf_name1 : {section1 : 'text', section2 : 'text', ... },
                        pdf_name2 : {section1 : 'text', section2 : 'text', ... }, ...}
    """

    # Get the text for each section for each pdf
    sections = [pdf_names]
    for section_folder in sections_folder_names:
        section_text = get_references_sections(
            pdf_names,
            '{}/{}'.format(
                sections_location,
                section_folder
                )
            )
        sections.append(section_text)

    sections_dict = {}
    for p, *r in zip(*sections):
        sections = {}
        for i, section_folder in enumerate(sections_folder_names):
            sections.update({section_folder : r[i]})
        sections_dict.update({p: sections})

    return sections_dict


def create_argparser():
    parser = ArgumentParser()
    parser.add_argument(
        '--verbose',
        help='Whether you want to print detailed test information ("True") or not ("False")',
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
        '{}/Test results - {:%Y-%m-%d-%H%M}'.format(settings.LOG_FILE_PREFIX, now), 'w'
        )
        
    log_file.write(
        'Date of test = {:%Y-%m-%d-%H%M}\n'.format(now)
        )

    logger.info('Reading files...')
    fm = FileManager()

    # Load data to test scraping for tests 1 and 2:
    logger.info('[+] Reading {}'.format(settings.SCRAPE_DATA_PDF_FOLDER_NAME))

    # Get the pdf names from the evaluate scraping folder:
    scrape_pdf_location = '{}/{}'.format(settings.FOLDER_PREFIX,settings.SCRAPE_DATA_PDF_FOLDER_NAME)
    pdf_names = listdir(scrape_pdf_location)
    pdf_names = [os.path.splitext(pdf_name)[0] for pdf_name in pdf_names]
    pdf_names.remove('.DS_Store')

    sections_location = '{}/{}'.format(settings.FOLDER_PREFIX,settings.SCRAPE_DATA_REF_PDF_FOLDER_NAME)
    sections_folder_names = [name for name in os.listdir(sections_location) if os.path.isdir('{}/{}'.format(sections_location, name))]

    scrape_test_data = get_sections_text_dict(pdf_names, sections_folder_names, sections_location)

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
    model = fm.get_file('reference_parser_pipeline.pkl','./reference_parser_models/','pickle')

    logger.info('\nStarting the tests...\n')

    logger.info('[+] Running tests 1 and 2')                     

    test1_scores, test2_scores = evaluate_find_section(scrape_test_data, scrape_pdf_location)

    logger.info('[+] Running test 3')
    test3_scores = evaluate_split_section(
        split_section_test_data,
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
            log_file.write("\n-----Information about test {}:-----\n".format(i))
            [log_file.write("\n"+k+"\n"+str(v)+"\n") for (k,v) in tests.items()]
    else:
        for i, tests in enumerate(test_scores_list):
            log_file.write("\nScore for test {}:\n".format(i))
            log_file.write(str(tests['Score']))

    log_file.close()

