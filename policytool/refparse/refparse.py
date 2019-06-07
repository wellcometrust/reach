"""This module let you parse and compare references from both a scraper output
and a list of publication.
"""

from argparse import ArgumentParser
from collections import namedtuple
from multiprocessing import Pool
from urllib.parse import urlparse
from functools import partial
import os
import time

import sentry_sdk
import pandas as pd
import numpy as np # Need for loading splitter model pipelines

from .utils import (FileManager,
                   FuzzyMatcher,
                   split_section,
                   structure_reference,
                   HardTextSearch)
from .models import DatabaseEngine
from .settings import settings


SectionedDocument = namedtuple(
    'SectionedDocument',
    ['section', 'uri', 'id']
)


def check_references_file(ref_file, references_file):
    assert 'title' in ref_file, (
        "ref_file.title not defined in " +
        references_file +
        " consider renaming current title column name 'title'"
    )
    assert 'uber_id' in ref_file, (
        "ref_file.uber_id not defined in " +
        references_file +
        " consider renaming current uber id column name to 'uber_id'"
    )


def transform_scraper_file(scraper_data):
    """Takes a pandas dataframe. Yields back individual
    SectionedDocument tuples.
    """
    for _, document in scraper_data.iterrows():
        if document["sections"]:

            section = document['sections']['Reference']
            yield SectionedDocument(
                section,
                document['uri'],
                document['hash']
            )

def transform_structured_references(
        splitted_references, structured_references,
        document_id, document_uri):
    # DataFrame is pushed here because
    # - fuzzy matcher needs a dataframe
    # - to_csv needs a dataframe
    # so instead of init the dataframe twice we do it here for now
    structured_references = pd.DataFrame(structured_references)
    structured_references['Document id'] = document_id
    structured_references['Document uri'] = document_uri

    structured_references['Reference id'] = [
        hash(reference)
        for reference in splitted_references
    ]
    return structured_references


def get_file(file_str, file_type, get_scraped=False):
    if file_str.startswith('s3://'):
        u = urlparse(file_str)
        fm = FileManager('S3', bucket=u.netloc)
        file_name = os.path.basename(u.path)
        file_dir = os.path.dirname(u.path)[1:]  # strip /
    else:
        fm = FileManager('LOCAL')
        file_name = os.path.basename(file_str)
        file_dir = os.path.dirname(file_str)
    if get_scraped:
        file = fm.get_scraping_results(
            file_name,
            file_dir,)
    else:
        file = fm.get_file(
            file_name,
            file_dir,
            file_type)
    return file


def remove_dups_and_concat(fuzzy_matches, text_matches):
    #Remove duplicate columns and short matches in the fuzzy matches
    fuzzy_matches = fuzzy_matches.loc[:,~fuzzy_matches.columns.duplicated()]

    if not fuzzy_matches.empty:
        fuzzy_matches = fuzzy_matches.loc[fuzzy_matches['WT_Ref_Title'].str.len() >= settings.MIN_CHAR_LIMIT]

    if text_matches.empty:
        return fuzzy_matches

    duplicate_ref_ids = fuzzy_matches['WT_Ref_Id'][fuzzy_matches['WT_Ref_Id'].isin(text_matches['WT_Ref_Id'])]

    #For duplicate matches: remove from text_matches, and renames 'Match_algorithm' in fuzzy_matches
    text_matches = text_matches[~text_matches['WT_Ref_Id'].isin(duplicate_ref_ids)]
    fuzzy_matches.at[fuzzy_matches['WT_Ref_Id'].isin(duplicate_ref_ids), 'Match_algorithm'] = "Fuzzy and Text Searches"

    all_matches = pd.concat([fuzzy_matches, text_matches])
    return all_matches


def yield_structured_references(scraper_file,
                model_file, splitter_model_file, pool_map, logger):
    """
    Parsers references using a (potentially parallelized) map()
    implementation, yielding back one dataframe for each document
    in scraper_file.

    Args:
        scraper_file: path / S3 url to scraper results file
        model_file: path/S3 url to model pickle file (three formats FTW!)
        splitter_model_file: path/S3 url to model dill file
        pool_map: (possibly parallel) implementation of map() builtin
        logger: logging configuration name
    """

    logger.info("[+] Reading input files")

    # Loading the scraper results
    scraper_file = get_file(scraper_file, "", get_scraped=True)
    
    # Loading the pipeline
    model = get_file(model_file, 'pickle')

    splitter_model = get_file(splitter_model_file, 'dill')

    sectioned_documents = transform_scraper_file(scraper_file)

    t0 = time.time()
    nb_references = 0
    for i, doc in enumerate(sectioned_documents):
        logger.info('[+] Processing references from document {}'.format(
            i
        ))

        splitted_references = split_section(
            doc.section,
            splitter_model
        )

        # For some weird reason not using pool map 
        #   in my laptop is more performant
        structured_references = pool_map(
            # A better name would be parse_reference
            #   here but we use it differently here
            partial(structure_reference, model),
            splitted_references
        )

        structured_references = transform_structured_references(
            splitted_references,
            structured_references,
            doc.id,
            doc.uri
        )
        yield doc.id, structured_references

        nb_references += len(splitted_references)

    t1 = time.time()
    total = t1-t0

    logger.info(
        "Time taken to predict for %s is %s",
        str(nb_references),
        str(total)
    )


def parse_references(scraper_file, model_file, splitter_model_file,
                     output_url, num_workers, logger):

    """
    Entry point for reference parser.

    Args:
        scraper_file: path / S3 url to scraper results file
        model_file: path/S3 url to model pickle file (three formats FTW!)
        spitter_model_file: path/S3 url to splitter model dill file
        num_workers: number of workers to use, or None for multiprocessing's
            default (number of cores).
        logger: logging configuration name
    """
    if num_workers == 1:
        pool = None
        pool_map = map
    else:
        pool = Pool(num_workers)
        pool_map = pool.map

    yield from yield_structured_references(
        scraper_file, model_file, splitter_model_file, pool_map, logger)

    if pool is not None:
        pool.terminate()
        pool.join()


def run_match(structured_references, fuzzy_matcher, text_matcher):
    matched_references_parser = fuzzy_matcher.fuzzy_match(
        structured_references
    )
    matched_references_hard_text = text_matcher.hard_text_search(
        doc
    )
    matched_references = remove_dups_and_concat(matched_references_parser, matched_references_hard_text)
    return matched_references



def match_references(scraper_file, references_file, model_file,
            splitter_model_file, output_url, num_workers, logger):

    # Loading the references file
    ref_file = get_file(references_file, 'csv')
    check_references_file(ref_file, references_file)

    fuzzy_matcher = FuzzyMatcher(
        ref_file,
        settings.FUZZYMATCH_THRESHOLD
    )
    text_matcher = HardTextSearch(ref_file)

    refs = parse_references(
        scraper_file, model_file, splitter_model_file, output_url, num_workers, logger)
    for doc_id, structured_references in refs:
        matched_references = run_match(
            structured_references,
            fuzzy_matcher,
            text_matcher)

        if output_url.startswith('file://'):
            # use everything after first two slashes; this handles
            # absolute and relative urls equally well
            output_dir = output_url[7:]
            structured_references.to_csv(
                os.path.join(
                    output_dir,
                    f"{doc_id}_{settings.PREF_REFS_FILENAME}"
                    )
                )
            matched_references.to_csv(
                os.path.join(
                    output_dir,
                    f"{doc_id}_{settings.MATCHES_FILENAME}"
                    )
                )
        else:
            database = DatabaseEngine(output_url)
            database.save_to_database(
                structured_references,
                matched_references,
            )



def match_references_profile(scraper_file, references_file,
                             model_file, splitter_model_file,
                             output_url, logger):
    """
    Entry point for reference parser, single worker, with profiling.

    Args:
        scraper_file: path / S3 url to scraper results file
        references_file: path/S3 url to references CSV file
        model_file: path/S3 url to model pickle file (three formats FTW!)
        splitter_model_file: path/S3 url to splitter model dill file
        output_url: file/S3 url for output files
    """
    import cProfile
    cProfile.run(
        ''.join([
            'match_references(scraper_file, references_file,',
            'model_file, splitter_model_file, output_url, 1, logger)'
        ]),
        'stats_dumps'
    )


def create_argparser(description):
    parser = ArgumentParser(description)
    parser.add_argument(
        '--references-file',
        help='Path or S3 URL to references CSV file to match against'
    )

    parser.add_argument(
        '--model-file',
        help='Path or S3 URL to model pickle file',
        default=os.path.join(
            settings.MODEL_DIR,
            settings.CLASSIFIER_FILENAME
            )
    )

    parser.add_argument(
        '--splitter-model-file',
        help='Path or S3 URL to splitter model dill file',
        default=os.path.join(
            settings.SPLIT_MODEL_DIR,
            settings.SPLITTER_FILENAME
            )
    )

    parser.add_argument(
        '--output-url',
        help='URL (file://!) or DSN for output',
        default=settings.OUTPUT_URL
    )

    parser.add_argument(
        '--num-workers',
        help='Number of workers to use for parallel processing.',
        type=int
    )

    return parser


if __name__ == '__main__':
    logger = settings.logger
    logger.setLevel('INFO')

    # SENTRY_DSN must be present at import time. If we don't have it then,
    # we won't have it later either.
    if 'SENTRY_DSN' in os.environ:
        logger.info("[+] Initialising Sentry")
        sentry_sdk.init(os.environ['SENTRY_DSN'])

    try:
        parser = create_argparser(description=__doc__.strip())
        parser.add_argument(
            '--scraper-file',
            help='Path or S3 URL to scraper results file',
            default=os.path.join(
                settings.SCRAPER_RESULTS_DIR,
                settings.SCRAPER_RESULTS_FILENAME
            )
        )

        parser.add_argument(
            '--profile',
            action='store_true',
            help='Run parser, single worker, with cProfile for profiling')
        args = parser.parse_args()

        if args.profile:
            assert args.num_workers is None or args.num_workers == 1

            match_references_profile(
                args.scraper_file,
                args.references_file,
                args.model_file,
                args.splitter_model_file,
                args.output_url,
                logger
            )
        else:
            match_references(
                args.scraper_file,
                args.references_file,
                args.model_file,
                args.splitter_model_file,
                args.output_url,
                args.num_workers,
                logger
            )

    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.error(e)
        raise
