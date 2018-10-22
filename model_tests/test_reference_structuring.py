import os
import pandas as pd
from datetime import datetime
from .test_settings import settings
from utils import load_pickle_file
from .tests_utils import test_structure


def test_reference_structuring(actual_reference_structures):
    """TEST 3 : Structuring of references
    Test how well a title was predicted in a reference.
    """

    logger = settings.logger
    now = datetime.now()
    mnb = load_pickle_file(settings.MODEL_DIR, settings.CLASSIFIER_FILENAME)
    vectorizer = load_pickle_file(
        settings.MODEL_DIR,
        settings.VECTORIZER_FILENAME
    )

    logger.info("============")
    logger.info(
        "Test 3 - How well reference components were predicted in a reference"
    )
    logger.info("============")

    similarity_scores = []
    test3_score = {}
    test3_infos = {}
    for organisation in settings.ORGANISATIONS:
        print("\n-----\n" + organisation + "\n-----\n")

        # Just use the data for the relevant source:
        this_actual_reference_structures = actual_reference_structures.loc[
            actual_reference_structures['Source'] == organisation
        ]

        # How well did it predict for each category of a reference?
        similarity_score, mean_similarity_score = test_structure(
            this_actual_reference_structures,
            settings.COMPONENTS_ID_NAME,
            settings.ACTUAL_PUBLICATION_ID_NAME,
            mnb, vectorizer)

        test3_info = "".join([
            "Average similarity scores between predicted and actual ",
            "references for each component, using a sample of ",
            "{} references: \n".format(len(this_actual_reference_structures)),
            "{}\n".format(mean_similarity_score),
            "Number of samples with predictions: ",
            str(mean_similarity_score['Number with a prediction']),
        ])
        logger.info(test3_info)

        test3_infos[organisation] = test3_info
        test3_score[organisation] = mean_similarity_score['Title']

        similarity_scores.append(similarity_score)

    similarity_scores = pd.concat(similarity_scores)
    similarity_scores.to_csv(
        os.path.join(
            settings.LOG_FILE_PREFIX,
            f"Test results - cosine sim of references comparison - {now}.csv"
        )
    )
    return test3_infos, test3_score
