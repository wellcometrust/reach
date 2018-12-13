"""This module let you parse and compare references from both a scraper output
and a list of publication.
"""

import time
import os
from argparse import ArgumentParser
import sentry_sdk
from utils import (FileManager,
                   FuzzyMatcher,
                   process_reference_section,
                   predict_references,
                   predict_structure)
from models import DatabaseEngine
from settings import settings


def run_predict(scraper_file, references_file,
                model_file, vectorizer_file):
    logger = settings.logger

    logger.setLevel('INFO')
    mode = 'S3' if settings.S3 else 'LOCAL'
    fm = FileManager(mode)
    logger.info("[+] Reading input files for %s", settings.ORGANISATION)

    # Loading the scraper results
    scraper_file_name = os.path.basename(scraper_file)
    scraper_file_dir = os.path.dirname(scraper_file)

    scraper_file = fm.get_scraping_results(
        scraper_file_name,
        scraper_file_dir,
    )

    # Loading the references file
    ref_file_name = os.path.basename(references_file)
    ref_file_dir = os.path.dirname(references_file)
    ref_file = fm.get_file(ref_file_name, ref_file_dir, 'csv')

    # Loading the model and the vectoriser
    model_file_name = os.path.basename(model_file)
    model_file_dir = os.path.dirname(model_file)
    mnb = fm.get_file(model_file_name, model_file_dir, 'pickle')

    vect_file_name = os.path.basename(vectorizer_file)
    vect_file_dir = os.path.dirname(vectorizer_file)
    vectorizer = fm.get_file(vect_file_name, vect_file_dir, 'pickle')

    # Split the reference sections using regex
    logger.info('[+] Spliting the references')
    splited_references = process_reference_section(
        scraper_file,
        settings.ORGANISATION_REGEX
    )

    t0 = time.time()

    # Predict the references types (eg title/author...)
    logger.info('[+] Predicting the reference components')
    reference_components_predictions = predict_references(
        mnb,
        vectorizer,
        splited_references
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

    if not settings.DEBUG:
        database = DatabaseEngine()
        database.save_to_database(
            predicted_reference_structures,
            all_match_data,
        )
    else:
        predicted_reference_structures.to_csv(
            os.path.join(
                settings.LOCAL_OUTPUT_DIR,
                settings.PREF_REFS_FILENAME
                )
            )
        all_match_data.to_csv(
            os.path.join(
                settings.LOCAL_OUTPUT_DIR,
                settings.MATCHES_FILENAME
                )
            )

    t1 = time.time()
    total = t1-t0

    logger.info(
        "Time taken to predict and match for %s is %s",
        str(len(splited_references)),
        str(total)
    )


if __name__ == '__main__':
    # SENTRY_DSN must be present at import time. If we don't have it then,
    # we won't have it later either.
    sentry_sdk.init(os.environ['SENTRY_DSN'])

    try:
        parser = ArgumentParser(description=__doc__.strip())
        parser.parse_args()

        scraper_file = os.path.join(
            settings.SCRAPER_RESULTS_DIR,
            settings.SCRAPER_RESULTS_FILENAME
        )

        references_file = os.path.join(
            settings.REFERENCES_DIR,
            settings.REFERENCES_FILENAME
        )

        model_file = os.path.join(
            settings.MODEL_DIR,
            settings.CLASSIFIER_FILENAME
        )

        vectorizer_file = os.path.join(
            settings.MODEL_DIR,
            settings.VECTORIZER_FILENAME
        )
        if settings.DEBUG:
            import cProfile
            cProfile.run(
                ''.join([
                    'run_predict(scraper_file, references_file,',
                    'model_file, vectorizer_file)'
                ]),
                'stats_dumps'
            )
        else:
            run_predict(scraper_file, references_file,
                        model_file, vectorizer_file)
    except Exception as e:
        sentry_sdk.capture_exception(e)
        raise
