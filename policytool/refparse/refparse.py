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
import json

import sentry_sdk
import pandas as pd

from .utils import (FileManager,
                   FuzzyMatcher,
                   split_section,
                   structure_reference,
                   ExactMatcher)
from .models import DatabaseEngine
from .settings import settings


SectionedDocument = namedtuple(
    'SectionedDocument',
    ['section', 'uri', 'id']
)


def check_publications_file(publications, publications_file):
    publications_df = pd.DataFrame(publications)
    assert 'title' in publications_df, (
        "title not defined in " +
        publications_file +
        " consider renaming current title column name 'title'"
    )
    assert 'uber_id' in publications_df, (
        "uber_id not defined in " +
        publications_file +
        " consider renaming current uber id column name to 'uber_id'"
    )


def transform_scraper_file(scraper_data):
    """Takes a pandas dataframe. Yields back individual
    SectionedDocument tuples.
    """
    for _, document in scraper_data.iterrows():
        if document["sections"]:
            try:
                sections = document['sections']['Reference']
            except KeyError:
                return
            assert isinstance(sections, list)
            for section in sections:
                yield SectionedDocument(
                    section,
                    None, # TODO: use document['uri'] after fixing scrape
                    document['file_hash']
                )

def transform_structured_references(
        splitted_references, structured_references,
        document_id, document_uri):
    transformed_structured_references = []
    for structured_reference, splitted_reference in zip(structured_references, splitted_references):
        # Don't return the structured references if no categories were found
        if any(structured_reference.values()):
            structured_reference['Document id'] = document_id
            structured_reference['Document uri'] = document_uri
            structured_reference['Reference id'] = hash(splitted_reference)
            transformed_structured_references.append(structured_reference)

    return transformed_structured_references


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


def yield_structured_references(scraper_file,
                model_file, pool_map, logger):
    """
    Parsers references using a (potentially parallelized) map()
    implementation, yielding back a list of reference dicts for each
    document in scraper_file.

    Args:
        scraper_file: path / S3 url to scraper results file
        model_file: path/S3 url to model pickle file (three formats FTW!)
        pool_map: (possibly parallel) implementation of map() builtin
        logger: logging configuration name
    """

    logger.info("[+] Reading input files")

    # Loading the scraper results
    scraper_file = get_file(scraper_file, "", get_scraped=True)
    
    # Loading the pipeline
    model = get_file(model_file, 'pickle')

    sectioned_documents = transform_scraper_file(scraper_file)

    t0 = time.time()
    nb_references = 0
    for i, doc in enumerate(sectioned_documents):
        logger.info('[+] Processing references from document {}'.format(
            i
        ))

        splitted_references = split_section(
            doc.section,
            settings.ORGANISATION_REGEX
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
        yield structured_references

        nb_references += len(splitted_references)

    t1 = time.time()
    total = t1-t0

    logger.info(
        "Time taken to predict for %s is %s",
        str(nb_references),
        str(total)
    )


def parse_references(scraper_file, model_file,
                     num_workers, logger):

    """
    Entry point for reference parser.

    Args:
        scraper_file: path / S3 url to scraper results file
        model_file: path/S3 url to model pickle file (three formats FTW!)
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
        scraper_file, model_file, pool_map, logger)

    if pool is not None:
        pool.terminate()
        pool.join()

#
# Module entry points
#

def fuzzy_match_reference(fuzzy_matcher, reference):
    """
    Args:
        fuzzy_matcher: instance of FuzzyMatcher, with index of publications in place.
        reference: reference

    Returns:
        matched reference (citations), including publication & doc id.
    """
    return fuzzy_matcher.match(reference)

def exact_match_publication(exact_matcher, publication):
    """
    Args:
        exact_matcher_matcher: instance of HardTextMatcher, with index of documents in place.
        publication: publication

    Returns:
        matched reference (citations), including publication & doc id.
    """
    return exact_matcher.match(publication)

#
# CLI functions
#

def run_match(scraper_file, publications_file, model_file,
              output_url, num_workers, logger):

    # Loading the references file
    publications_df = get_file(publications_file, 'csv')
    publications = publications_df.to_dict('records')
    check_publications_file(publications, publications_file)

    assert output_url.startswith('file://')
    output_dir = output_url[7:]

    structured_references_filepath = os.path.join(
        output_dir,
        f"{settings.STRUCTURED_REFS_FILENAME}"
    )
    fuzzy_matched_references_filepath = os.path.join(
        output_dir,
        f"fuzzy_{settings.MATCHED_REFS_FILENAME}"
    )
    exact_matched_reference_filepath = os.path.join(
        output_dir,
        f"exact_{settings.MATCHED_REFS_FILENAME}"
    )

    fuzzy_matcher = FuzzyMatcher(
        publications,
        settings.FUZZYMATCH_SIMILARITY_THRESHOLD
    )

    with open(structured_references_filepath, 'w') as srefs_f:
        with open(fuzzy_matched_references_filepath, 'w') as fmrefs_f:

            refs = parse_references(
                scraper_file, model_file, num_workers, logger)
            for structured_references in refs:
                for structured_reference in structured_references:

                    fuzzy_matched_reference = fuzzy_match_reference(
                        fuzzy_matcher,
                        structured_reference
                    )
                    if fuzzy_matched_reference:
                        fmrefs_f.write(json.dumps(fuzzy_matched_reference)+'\n')
                    if structured_reference:
                        srefs_f.write(json.dumps(structured_reference)+'\n')

    scraper_file = get_file(scraper_file, "", get_scraped=True)
    sectioned_documents = transform_scraper_file(scraper_file)
    exact_matcher = ExactMatcher(sectioned_documents, settings.MATCH_TITLE_LENGTH_THRESHOLD)
    with open(exact_matched_reference_filepath, 'w') as emrefs_f: 
        for publication in publications:
            exact_matched_references = exact_match_publication(exact_matcher, publication)
            for exact_matched_reference in exact_matched_references:
                if exact_matched_reference:
                    emrefs_f.write(json.dumps(exact_matched_reference)+'\n')


def run_match_profile(scraper_file, references_file,
                             model_file, output_url, logger):
    """
    Entry point for reference parser, single worker, with profiling.

    Args:
        scraper_file: path / S3 url to scraper results file
        references_file: path/S3 url to references CSV file
        model_file: path/S3 url to model pickle file (three formats FTW!)
        output_url: file/S3 url for output files
    """
    import cProfile
    cProfile.run(
        ''.join([
            'run_match(scraper_file, references_file,',
            'model_file, output_url, 1, logger)'
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

            run_match_profile(
                args.scraper_file,
                args.references_file,
                args.model_file,
                args.output_url,
                logger
            )
        else:
            run_match(
                args.scraper_file,
                args.references_file,
                args.model_file,
                args.output_url,
                args.num_workers,
                logger
            )

    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.error(e)
        raise
