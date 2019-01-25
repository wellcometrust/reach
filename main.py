"""This module let you parse and compare references from both a scraper output
and a list of publication.
"""

from argparse import ArgumentParser
from urllib.parse import urlparse
import time
import os
import sentry_sdk

from utils import (FileManager,
                   FuzzyMatcher,
                   process_reference_section,
                   process_references,
                   predict_references,
                   predict_structure)
from models import DatabaseEngine
from settings import settings



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
    sections_data = []
    for _, document in scraper_data.iterrows():
        if document["sections"]:

            section = document['sections']['Reference']
            
            sections_data.append({
                'Section': section,
                'Document uri': document['uri'],
                'Document id': document['hash']
            })
    return sections_data

def get_file(file_str, file_type, get_scraped = False):
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

def run_predict(scraper_file, references_file,
                model_file, vectorizer_file,
                output_url):
 
    logger.info("[+] Reading input files for %s", settings.ORGANISATION)

    # Loading the scraper results
    scraper_file = get_file(scraper_file, "", get_scraped=True)

    # Loading the references file
    ref_file = get_file(references_file, 'csv')
    check_references_file(ref_file, references_file)

    # Loading the model and the vectoriser
    mnb = get_file(model_file, 'pickle')
    vectorizer = get_file(vectorizer_file, 'pickle')

    # Split the reference sections using regex
    logger.info('[+] Spliting the references')
    sections_data = transform_scraper_file(scraper_file)
    splited_references = process_reference_section(
        sections_data,
        settings.ORGANISATION_REGEX
    )
    splited_components = process_references(splited_references)
    t0 = time.time()

    # Predict the references types (eg title/author...)
    logger.info('[+] Predicting the reference components')
    reference_components_predictions = predict_references(
        mnb,
        vectorizer,
        splited_components
    )

    # Predict the reference structure????
    predicted_reference_structures = predict_structure(
        reference_components_predictions,
        settings.PREDICTION_PROBABILITY_THRESHOLD
    )

    fuzzy_matcher = FuzzyMatcher(
        ref_file,
        settings.FUZZYMATCH_THRESHOLD
    )
    all_match_data = fuzzy_matcher.fuzzy_match_blocks(
        settings.BLOCKSIZE,
        predicted_reference_structures,
        settings.FUZZYMATCH_THRESHOLD
    )

    if output_url.startswith('file://'):
        # use everything after first two slashes; this handles
        # absolute and relative urls equally well
        output_dir = output_url[7:]
        predicted_reference_structures.to_csv(
            os.path.join(
                output_dir,
                settings.PREF_REFS_FILENAME
                )
            )
        all_match_data.to_csv(
            os.path.join(
                output_dir,
                settings.MATCHES_FILENAME
                )
            )
    else:
        database = DatabaseEngine(output_url)
        database.save_to_database(
            predicted_reference_structures,
            all_match_data,
        )

    t1 = time.time()
    total = t1-t0

    logger.info(
        "Time taken to predict and match for %s is %s",
        str(len(splited_references)),
        str(total)
    )


if __name__ == '__main__':
    logger = settings.logger
    logger.setLevel('INFO')

    # SENTRY_DSN must be present at import time. If we don't have it then,
    # we won't have it later either.
    if 'SENTRY_DSN' in os.environ:
        logger.info("[+] Initialising Sentry")
        sentry_sdk.init(os.environ['SENTRY_DSN'])

    try:
        parser = ArgumentParser(description=__doc__.strip())
        parser.add_argument(
            '--scraper-file',
            help='Path or S3 URL to scraper results file'
        )
        parser.add_argument(
            '--references-file',
            help='Path or S3 URL to references CSV file to match against'
        )
        parser.add_argument(
            '--model-file',
            help='Path or S3 URL to model pickle file'
        )
        parser.add_argument(
            '--vectorizer-file',
            help='Path or S3 URL to vectorizer pickle file'
        )
        parser.add_argument(
            '--output-url',
            help='URL (file://!) or DSN for output'
        )
        args = parser.parse_args()

        if args.scraper_file is None:
            scraper_file = os.path.join(
                settings.SCRAPER_RESULTS_DIR,
                settings.SCRAPER_RESULTS_FILENAME
            )
        else:
            scraper_file = args.scraper_file

        if args.references_file is None:
            references_file = os.path.join(
                settings.REFERENCES_DIR,
                settings.REFERENCES_FILENAME
            )
        else:
            references_file = args.references_file

        if args.model_file is None:
            model_file = os.path.join(
                settings.MODEL_DIR,
                settings.CLASSIFIER_FILENAME
            )
        else:
            model_file = args.model_file

        if args.vectorizer_file is None:
            vectorizer_file = os.path.join(
                settings.MODEL_DIR,
                settings.VECTORIZER_FILENAME
            )
        else:
            vectorizer_file = args.vectorizer_file

        if args.output_url is None:
            output_url = settings.OUTPUT_URL
            #os.path.join(
            #    settings.REFERENCES_DIR,
            #    settings.REFERENCES_FILENAME
            #)
        else:
            output_url = args.output_url

        if settings.DEBUG:
            import cProfile
            cProfile.run(
                ''.join([
                    'run_predict(scraper_file, references_file,',
                    'model_file, vectorizer_file, output_url)'
                ]),
                'stats_dumps'
            )
        else:
            run_predict(scraper_file, references_file,
                        model_file, vectorizer_file, output_url)
    except Exception as e:
        sentry_sdk.capture_exception(e)
        raise
