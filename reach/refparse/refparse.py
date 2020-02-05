"""This module let you parse and compare references from both a scraper output
and a list of publication.
"""

from argparse import ArgumentParser
from collections import namedtuple
from multiprocessing import Pool
from urllib.parse import urlparse
from functools import partial
import os
import os.path
import time
import json

import sentry_sdk
import pandas as pd

from .utils import (FileManager,
                   FuzzyMatcher,
                   structure_reference,
                   ExactMatcher)
from .settings import settings

from deep_reference_parser.split_section import SplitSection


SectionedDocument = namedtuple(
    'SectionedDocument',
    ['section', 'uri', 'id', 'metadata']
)

DEFAULT_MODEL_FILE = os.path.join(
    os.path.dirname(__file__),
    'reference_parser_models',
    'reference_parser_pipeline.pkl'
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


def transform_scraper_file(scraper_data, section_column="sections"):
    """Takes a pandas dataframe. Yields back individual
    SectionedDocument tuples.
    """
    for _, document in scraper_data.iterrows():
        if document[section_column]:
            try:
                sections = document[section_column]
            except KeyError:
                return
            for section_list in sections.values():
                assert isinstance(section_list, list)
                for section in section_list:
                    yield SectionedDocument(
                        section,
                        document.get('url', None),
                        document['file_hash'],
                        dict(document)
                    )

def transform_scraper_text_file(scraper_data, text_column="text"):
    """Takes a pandas dataframe. Yields back individual
    SectionedDocument tuples.
    """
    for _, document in scraper_data.iterrows():
        metadata = {}
        metadata.update(document.get("source_metadata", {}))
        metadata.update(document.get("pdf_metadata", {}))
        if document[text_column]:
            text = document[text_column]
            yield SectionedDocument(
                text,
                document.get('url', None),
                document['file_hash'],
                metadata
            )

def transform_structured_references(
        splitted_references, structured_references,
        document_id, document_uri, document_metadata):
    transformed_structured_references = []
    for structured_reference, splitted_reference in zip(structured_references, splitted_references):
        # Don't return the structured references if no categories were found
        if any(structured_reference.values()):
            structured_reference['document_id'] = document_id
            structured_reference['document_url'] = document_uri
            structured_reference['reference_id'] = hash(splitted_reference)
            structured_reference['metadata'] = dict((key, value) for key, value in document_metadata.items() if key != 'sections')
            transformed_structured_references.append(structured_reference)

    return transformed_structured_references

SCRAPING_COLUMNS = [
    'title',
    'file_hash',
    'sections',
    'url',
    'keywords',
    'source_page',
    'authors',
    'subject',
    'year',
    'created',
    'types'
]

def get_file(
        file_str,
        file_type,
        get_scraped=False,
        scraping_columns=('title', 'file_hash', 'sections', 'uri', 'url', 'keywords')
        ):
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
            file_dir,
            SCRAPING_COLUMNS,)
    else:
        file = fm.get_file(
            file_name,
            file_dir,
            file_type)
    return file


def yield_structured_references(scraper_file,
                pool_map, logger, model_file=DEFAULT_MODEL_FILE):
    """
    Parsers references using a (potentially parallelized) map()
    implementation, yielding back a list of reference dicts for each
    document in scraper_file.

    Args:
        scraper_file: path / S3 url to scraper results file
        pool_map: (possibly parallel) implementation of map() builtin
        logger: logging configuration name
        model_file: path/S3 url to model pickle file.
            Defaults to model within our source tree.
    """

    logger.info("[+] Reading input files")

    # Loading the scraper results
    scraper_file = get_file(scraper_file, "", get_scraped=True)

    # Loading the pipeline
    model = get_file(model_file, 'pickle')

    sectioned_documents = transform_scraper_file(scraper_file)

    # Instantiate deep_reference_parser model here (not in loop!)

    section_splitter = SplitSection()

    t0 = time.time()
    nb_references = 0
    for i, doc in enumerate(sectioned_documents):
        logger.info('[+] Processing references from document {}'.format(
            i
        ))

        splitted_references = section_splitter.split(
            doc.section
        )

        logger.info('[+] Extracted {} references from document {}'.format(
            len(splitted_references),
            i
        ))

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
            doc.uri,
            doc.metadata
        )

        splitted_references = {
            "doc_id": doc.id,
            "doc_url": doc.uri,
            "references": splitted_references
        }
        yield splitted_references, structured_references

        nb_references += len(splitted_references)

    t1 = time.time()
    total = t1-t0

    logger.info(
        "Time taken to predict for %s is %s",
        str(nb_references),
        str(total)
    )


def parse_references(scraper_file, model_file, num_workers, logger):

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
        scraper_file, pool_map, logger, model_file)

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

def refparse(scraper_file, publications_file, model_file,
              output_dir, num_workers, logger):

    # Loading the references file
    publications_df = get_file(publications_file, 'csv')
    publications = publications_df.to_dict('records')
    check_publications_file(publications, publications_file)

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

    scraper_file = get_file(
        scraper_file, "",
        get_scraped=True,
        scraping_columns=('title', 'file_hash', 'uri', 'text')
        )

    document_texts = transform_scraper_text_file(scraper_file)
    exact_matcher = ExactMatcher(document_texts, settings.MATCH_TITLE_LENGTH_THRESHOLD)

    with open(exact_matched_reference_filepath, 'w') as emrefs_f:
        for publication in publications:
            exact_matched_references = exact_match_publication(exact_matcher, publication)
            for exact_matched_reference in exact_matched_references:
                if exact_matched_reference:
                    emrefs_f.write(json.dumps(exact_matched_reference)+'\n')

def refparse_profile(scraper_file, references_file,
                             model_file, output_dir, logger):
    """
    Entry point for reference parser, single worker, with profiling.

    Args:
        scraper_file: path / S3 url to scraper results file
        references_file: path/S3 url to references CSV file
        model_file: path/S3 url to model pickle file (three formats FTW!)
        output_dir: file/S3 url for output files
    """
    import cProfile
    cProfile.run(
        ''.join([
            'refparse(scraper_file, references_file,',
            'model_file, output_dir, 1, logger)'
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
        default=DEFAULT_MODEL_FILE
    )

    parser.add_argument(
        '--output-dir',
        help='Path or S3 URL for output',
        default='.'
    )

    parser.add_argument(
        '--num-workers',
        help='Number of workers to use for parallel processing.',
        type=int
    )

    return parser


if __name__ == '__main__':
    import logging
    logging.basicConfig(format='[%(asctime)s]:%(levelname)s - %(message)s')
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

            refparse_profile(
                args.scraper_file,
                args.references_file,
                args.model_file,
                args.output_dir,
                logger
            )
        else:
            refparse(
                args.scraper_file,
                args.references_file,
                args.model_file,
                args.output_dir,
                args.num_workers,
                logger
            )

    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.error(e)
        raise
