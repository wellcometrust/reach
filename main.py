import time
import os
from utils import (FileManager, FuzzyMatcher, process_reference_section,
                   Predicter)
from models import DatabaseEngine
from settings import settings


def run_predict(scraper_file, references_file,
                model_file, vectorizer_file):
    logger = settings.logger
    mode = 'S3' if not settings.DEBUG else 'LOCAL'
    fm = FileManager(mode)
    predicter = Predicter()
    logger.info("Reading input files for %s", settings.ORGANISATION)

    scraper_file_name = os.path.basename(scraper_file)
    scraper_file_dir = os.path.dirname(scraper_file)
    raw_text_data = fm.get_file(scraper_file_name, scraper_file_dir, 'json')

    ref_file_name = os.path.basename(references_file)
    ref_file_dir = os.path.dirname(references_file)
    WT_references = fm.get_file(ref_file_name, ref_file_dir, 'csv')

    model_file_name = os.path.basename(model_file)
    model_file_dir = os.path.dirname(model_file)
    mnb = fm.get_file(model_file_name, model_file_dir, 'pickle')

    vect_file_name = os.path.basename(model_file)
    vect_file_dir = os.path.dirname(model_file)
    vectorizer = fm.get_file(vect_file_name, vect_file_dir, 'pickle')

    reference_components = process_reference_section(
        raw_text_data,
        settings.ORGANISATION_REGEX
    )

    t0 = time.time()

    reference_components_predictions = predicter.predict_references(
        mnb,
        vectorizer,
        reference_components
    )

    predicted_reference_structures = predicter.predict_structure(
        reference_components_predictions,
        settings.PREDICTION_PROBABILITY_THRESHOLD
    )
    predicted_reference_structures['Organisation'] = settings.ORGANISATION

    fuzzy_matcher = FuzzyMatcher(
        WT_references,
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

    t1 = time.time()
    total = t1-t0

    logger.info(
        "Time taken to predict and match for ",
        str(len(reference_components)),
        " is ", str(total)
    )


if __name__ == '__main__':

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

    run_predict(scraper_file, references_file, model_file, vectorizer_file)
