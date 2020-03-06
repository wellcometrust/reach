"""
e.g. python evaluate_algo.py --verbose True
"""

import json
import logging
import os
import time
from argparse import ArgumentParser
from collections import defaultdict
from datetime import datetime
from os import listdir
from urllib.parse import urlparse

import pandas as pd
from reach.refparse.algo_evaluation.evaluate_find_section import \
    evaluate_find_section
from reach.refparse.algo_evaluation.evaluate_match_references import \
    evaluate_match_references
from reach.refparse.algo_evaluation.evaluate_parse import evaluate_parse
from reach.refparse.algo_evaluation.evaluate_settings import settings
from reach.refparse.algo_evaluation.evaluate_split_section import \
    evaluate_split_section
from reach.refparse.utils import FileManager

logging.basicConfig(
    format="%(asctime)s %(name)s %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.DEBUG,
)

def get_text(filepath):
    try:
        references_section = open(filepath).read()
    except FileNotFoundError:
        logger.warning("File %s does not exist", filepath)
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
    logger.setLevel(logging.INFO)

    logger.info('Starting evaluations...')

    log_file = open(
        '{}/Evaluation results - {:%Y-%m-%d-%H%M}.txt'.format(
            settings.LOG_FILE_PREFIX, now
        ), 'w'
    )

    log_file.write(
        'Date of evaluation = {:%Y-%m-%d-%H%M}\n'.format(now)
    )

    logger.info('main: Reading files...')
    fm = FileManager()

    # ==== Load data to evaluate scraping: ====
    start = time.time()
    logger.info('main: Reading %s',
        os.path.join(
            settings.FOLDER_PREFIX,
            settings.SCRAPE_DATA_PDF_FOLDER_NAME
        )
    )

    scrape_pdf_location = os.path.join(
        settings.FOLDER_PREFIX,
        settings.SCRAPE_DATA_PDF_FOLDER_NAME
    )

    sections_location = os.path.join(
        settings.FOLDER_PREFIX,
        settings.SCRAPE_DATA_REF_PDF_FOLDER_NAME
    )

    provider_names = fm.get_file(
        settings.SCRAPE_DATA_PROVIDERS_FILE_NAME,
        settings.FOLDER_PREFIX,
        'csv'
    )
    # Convert to dictionary for ease of use
    provider_names = provider_names.set_index('file_hash')['name'].to_dict()

    evaluate_find_section_data = defaultdict(lambda: defaultdict(str))

    for pdf_hash, section_name, section_text in yield_section_data(
            scrape_pdf_location, sections_location
        ):

        evaluate_find_section_data[pdf_hash][section_name] = section_text

    logger.info('main: ---> Took %0.3f seconds', time.time() - start)

    # ==== Load data to evaluate split sections: ====
    start = time.time()
    logger.info('main: Reading %s', settings.NUM_REFS_FILE_NAME)
    evaluate_split_section_data = fm.get_file(
        settings.NUM_REFS_FILE_NAME,
        settings.FOLDER_PREFIX,
        'csv'
    )

    # Add the complete reference section to the dataframe by loading from a file
    # downloaded from s3, and stored locally

    split_section_data = []
    section_path = os.path.join(
        settings.FOLDER_PREFIX,
        settings.NUM_REFS_TEXT_FOLDER_NAME
        )

    for doc_hash in evaluate_split_section_data['hash']:
        path = os.path.join(section_path, f'{doc_hash}.txt')
        text = None
        if os.path.isfile(path):
            text = get_text(path)
        split_section_data.append(text)

    evaluate_split_section_data['Reference section'] = split_section_data

    # Subset the evaluation data to prevent IndexError described in
    # https://github.com/wellcometrust/reach/issues/249

    evaluate_split_section_data.dropna(subset=['Reference section'],
        inplace=True)

    logger.info('main: ---> Took %0.3f seconds', time.time() - start)

    # ==== Load data to evaluate parse: ====
    start = time.time()
    logger.info('main: Reading %s', settings.PARSE_REFERENCE_FILE_NAME)
    evaluate_parse_data = fm.get_file(
        settings.PARSE_REFERENCE_FILE_NAME,
        settings.FOLDER_PREFIX,
        'csv'
    )
    # Load the latest parser model
    model = fm.get_file(
        settings.MODEL_FILE_NAME,
        settings.MODEL_FILE_PREFIX,
        settings.MODEL_FILE_TYPE
    )
    logger.info('main: ---> Took %0.3f seconds', time.time() - start)

    # ==== Load data to evaluate matching: ====
    start = time.time()
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
    logger.info('main: ---> Took %0.3f seconds', time.time() - start)

    # # ==== Get the evaluation metrics ====
    logger.info('\nStarting the evaluations...\n')

    start = time.time()
    logger.info('main: Running find references section evaluation')
    eval_scores_find = evaluate_find_section(
        evaluate_find_section_data,
        provider_names,
        scrape_pdf_location,
        settings.LEVENSHTEIN_DIST_SCRAPER_THRESHOLD
    )
    logger.info('main: ---> Took %0.3f seconds', time.time() - start)

    start = time.time()
    logger.info('main: Running split section evaluation')
    eval_score_split = evaluate_split_section(
        evaluate_split_section_data,
        settings.SPLIT_SECTION_SIMILARITY_THRESHOLD
        )
    logger.info('main: ---> Took %0.3f seconds', time.time() - start)

    start = time.time()
    logger.info('main: Running parse references evaluation')
    eval_score_parse = evaluate_parse(
        evaluate_parse_data,
        model,
        settings.LEVENSHTEIN_DIST_PARSE_THRESHOLD
        )
    logger.info('main: ---> Took %0.3f seconds', time.time() - start)

    start = time.time()
    logger.info('main: Running match references evaluation')
    eval_score_match = evaluate_match_references(
        evaluation_references,
        settings.MATCH_THRESHOLD,
        settings.LENGTH_THRESHOLD,
        settings.EVAL_SAMPLE_MATCH_NUMBER
        )
    logger.info('main: ---> Took %0.3f seconds', time.time() - start)

    eval_scores_list = [
        eval_scores_find,
        eval_score_split,
        eval_score_parse,
        eval_score_match
        ]

    eval_names = [
        "How well the scraper finds the references section",
        "How well the splitter predicted how many references there were",
        "How well the parser predicted reference component texts",
        "How well the matcher matched references"
    ]

    if eval(args.verbose):
        for i, evals in enumerate(eval_scores_list):
            log_file.write(
                "\n-----{}:-----\n".format(eval_names[i])
            )
            [
                log_file.write(
                    "\n"+k+"\n"+str(v)+"\n"
                ) for (k,v) in evals.items()
            ]
    else:
        for i, evals in enumerate(eval_scores_list):
            log_file.write("\n{} - Score:\n".format(eval_names[i]))
            log_file.write("{}\n".format(round(evals['Score'],2)))

    log_file.close()
