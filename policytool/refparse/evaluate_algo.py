"""
e.g. python evaluate_algo.py --verbose True
"""

from argparse import ArgumentParser
import os
import json
from os import listdir 
from datetime import datetime
from urllib.parse import urlparse
from collections import defaultdict

import pandas as pd

from policytool.refparse.utils import FileManager
from policytool.refparse.algo_evaluation.evaluate_settings import settings
from policytool.refparse.algo_evaluation.evaluate_find_section import evaluate_find_section
from policytool.refparse.algo_evaluation.evaluate_split_section import evaluate_split_section
from policytool.refparse.algo_evaluation.evaluate_parse import evaluate_parse
from policytool.refparse.algo_evaluation.evaluate_match_references import evaluate_match_references


def get_text(filepath):
    try:
        references_section = open(filepath).read()
    except:
        references_section = ""

    return references_section

def yield_section_data(scrape_pdf_location, sections_location):
    """
    sections_location and scrape_pdf_location both contain
    '.DS_Store' files, so I make sure to not include any
    hidden files (start with .)
    """
    sections_names = [
        section_name
        for section_name in listdir(sections_location)
        if not section_name.startswith('.')
    ]
    for filename in listdir(scrape_pdf_location):
        if not filename.startswith('.'):
            pdf_hash, _ = os.path.splitext(filename)
            for section_name in sections_names:
                section_path = os.path.join(sections_location, section_name, pdf_hash)
                section_text = get_text('{}.txt'.format(section_path))
                yield pdf_hash, section_name, section_text

def yield_pubs_json(pubs_file, total_N):

    # ==== Load data to evaluate matching: ====

    output_cols = ['title', 'pmid']
    with open(pubs_file, "r") as f:
        references = []
        for i, line in enumerate(f):
            if i >= total_N:
                break
            reference = json.loads(line)
            if all([output_col in reference for output_col in output_cols]):
                yield {
                    'Document id': i,
                    'title': reference['title'],
                    'Reference id':  reference['pmid'],
                    'uber_id':  reference['pmid']
                }

def create_argparser():
    parser = ArgumentParser()
    parser.add_argument(
        '--verbose',
        help='Whether you want to print detailed evaluation \
            information ("True") or not ("False")',
        default = 'True'
    )

    return parser

if __name__ == '__main__':

    parser = create_argparser()
    args = parser.parse_args()

    now = datetime.now()
    logger = settings.logger
    logger.setLevel('INFO')

    logger.info('Starting evaluations...')

    log_file = open(
        '{}/Evaluation results - {:%Y-%m-%d-%H%M}'.format(
            settings.LOG_FILE_PREFIX, now
        ), 'w'
    )
        
    log_file.write(
        'Date of evaluation = {:%Y-%m-%d-%H%M}\n'.format(now)
    )

    logger.info('main: Reading files...')
    fm = FileManager()

    # ==== Load data to evaluate scraping for evaluations 1 and 2: ====
    logger.info('main: Reading %s',
        settings.SCRAPE_DATA_PDF_FOLDER_NAME
    )

    scrape_pdf_location = os.path.join(
        settings.FOLDER_PREFIX,
        settings.SCRAPE_DATA_PDF_FOLDER_NAME
    )

    sections_location = os.path.join(
        settings.FOLDER_PREFIX,
        settings.SCRAPE_DATA_REF_PDF_FOLDER_NAME
    )

    evaluate_find_section_data = defaultdict(lambda: defaultdict(str))
    for pdf_hash, section_name, section_text in yield_section_data(
        scrape_pdf_location, sections_location):
        evaluate_find_section_data[pdf_hash][section_name] = section_text

    # ==== Load data to evaluate split sections for evaluations 3: ====
    logger.info('main: Reading %s', settings.NUM_REFS_FILE_NAME)
    evaluate_split_section_data = fm.get_file(
        settings.NUM_REFS_FILE_NAME,
        settings.FOLDER_PREFIX,
        'csv'
    )

    evaluate_split_section_data['Reference section'] = [
        get_text(
            '{}.txt'.format(
                os.path.join(
                    settings.FOLDER_PREFIX,
                    settings.NUM_REFS_TEXT_FOLDER_NAME,
                    doc_hash
                    )
                )
            ) for doc_hash in evaluate_split_section_data['hash']
        ]

    # ==== Load data to evaluate parse for evaluations 4: ====
    logger.info('main: Reading %s', settings.PARSE_REFERENCE_FILE_NAME)
    evaluate_parse_data = fm.get_file(
        settings.PARSE_REFERENCE_FILE_NAME,
        settings.FOLDER_PREFIX,
        'csv'
    )

    # ==== Load data to evaluate matching for evaluations 5: ====

    logger.info('main: Reading the first %d lines of %s',
        settings.EVAL_MATCH_NUMBER,
        settings.EVAL_PUB_DATA_FILE_NAME
        )
    pubs_file = os.path.join(
        settings.FOLDER_PREFIX,
        settings.EVAL_PUB_DATA_FILE_NAME
        )
    evaluation_references = [p for p in yield_pubs_json(
        pubs_file, settings.EVAL_MATCH_NUMBER
        )
    ]
    evaluation_references = pd.DataFrame(evaluation_references)
    
    # Load the latest parser model
    model = fm.get_file(
        settings.MODEL_FILE_NAME,
        settings.MODEL_FILE_PREFIX,
        settings.MODEL_FILE_TYPE
    )

    # # ==== Get the evaluation metrics ====
    logger.info('\nStarting the evaluations...\n')

    logger.info('main: Running evaluations 1 and 2')                     
    eval1_scores, eval2_scores = evaluate_find_section(
        evaluate_find_section_data,
        scrape_pdf_location,
        settings.LEVENSHTEIN_DIST_SCRAPER_THRESHOLD
    )

    logger.info('main: Running evaluation 3')
    eval3_scores = evaluate_split_section(
        evaluate_split_section_data,
        settings.ORGANISATION_REGEX,
        settings.SPLIT_SECTION_SIMILARITY_THRESHOLD
        )

    logger.info('main: Running evaluation 4')
    eval4_scores = evaluate_parse(
        evaluate_parse_data,
        model,
        settings.LEVENSHTEIN_DIST_PARSE_THRESHOLD
        )

    logger.info('main: Running evaluation 5')
    eval5_scores = evaluate_match_references(
        evaluation_references,
        settings.MATCH_THRESHOLD,
        settings.LENGTH_THRESHOLD,
        settings.EVAL_SAMPLE_MATCH_NUMBER
        )

    eval_scores_list = [
        eval1_scores,
        eval2_scores,
        eval3_scores,
        eval4_scores,
        eval5_scores
        ]

    if eval(args.verbose):
        for i, evals in enumerate(eval_scores_list):
            log_file.write(
                "\n-----Information about evaluation {}:-----\n".format(i+1)
            )
            [
                log_file.write(
                    "\n"+k+"\n"+str(v)+"\n"
                ) for (k,v) in evals.items()
            ]
    else:
        for i, evals in enumerate(eval_scores_list):
            log_file.write("\nScore for evaluation {}:\n".format(i+1))
            log_file.write("{}\n".format(round(evals['Score'],2)))

    log_file.close()

