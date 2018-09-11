import time
from utils import (FileManager, FuzzyMatcher, process_reference_section,
                   Predicter)
from models import DatabaseEngine
from settings import settings


logger = settings.logger
mode = 'S3' if not settings.DEBUG else 'LOCAL'
fm = FileManager(mode)
predicter = Predicter()
logger.info("Reading input files for %s", settings.ORGANISATION)

raw_text_data = fm.get_file(
    settings.SCRAPER_RESULTS_DIR,
    settings.SCRAPER_RESULTS_FILENAME,
    'json'
)

WT_references = fm.get_file(
    settings.REFERENCES_DIR,
    settings.REFERENCES_FILENAME,
    'csv'
)

mnb = fm.get_file(
    settings.MODEL_DIR,
    settings.CLASSIFIER_FILENAME,
    'pickle'
)
vectorizer = fm.get_file(
    settings.MODEL_DIR,
    settings.VECTORIZER_FILENAME,
    'pickle'
)

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
