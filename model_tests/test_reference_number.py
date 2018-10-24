import os
import pandas as pd
from datetime import datetime
from .test_settings import settings
from utils import FileManager
from .tests_utils import test_number_refs


def test_reference_number(actual_number_refs):
    """TEST 2 : Number of references
    Test how well the number of refs were predicted.
    """

    fm = FileManager()
    now = datetime.now()
    logger = settings.logger

    logger.info("============")
    logger.info("Test 2 - How well the number of refs were predicted")
    logger.info("============")

    comparisons = []
    test2_score = {}
    test2_infos = {}
    for organisation in settings.ORGANISATIONS:
        logger.info(organisation + "\n-----\n")

        # Just use the data for the relevant source:
        this_actual_number_refs = actual_number_refs.loc[
            actual_number_refs['Source'] == organisation
        ]

        # Select the policy documents which were manually tested
        sample_uri_number_refs = set(
            this_actual_number_refs[settings.ACTUAL_PUBLICATION_ID_NAME]
        )

        try:
            # Get the raw data for this organisation:
            raw_text_data = fm.get_file(
                "{}.json".format(organisation),
                settings.FOLDER_PREFIX,
                'json'
            )
        except FileNotFoundError:
            logger.warning(f'No file found for {organisation}')
            continue

        # Predict how many references these policy documents have
        raw_text_data_sample_number_refs = raw_text_data[raw_text_data[
            settings.RAW_PUBLICATION_ID_NAME
        ].isin(sample_uri_number_refs)]

        mean_difference_per, comparison = test_number_refs(
            raw_text_data_sample_number_refs,
            this_actual_number_refs,
            settings._regex_dict[organisation],
            settings.ACTUAL_PUBLICATION_ID_NAME,
            settings.COMPONENTS_ID_NAME
        )

        comparison['Source'] = organisation

        number_correct = len(
            comparison.loc[
                comparison[
                    'Difference as proportion of actual number'
                ] <= settings.TEST2_THRESH
            ]
        )

        test2_info = str(
            "Average difference between actual and predicted number of " +
            "references as proportion of actual number is " +
            str(round(mean_difference_per, 4)) + "\n" +
            "Proportion of test references with close to the same " +
            "actual and predicted number of references (difference <= " +
            str(settings.TEST2_THRESH) + ") = " +
            str(round(number_correct/len(comparison), 4)))
        print(test2_info)

        test2_infos[organisation] = test2_info

        test2_score[organisation] = number_correct/len(comparison)
        comparisons.append(comparison)

    comparisons = pd.concat(comparisons)
    comparisons.to_csv(
        os.path.join(
            settings.LOG_FILE_PREFIX,
            f"Test results - number of references comparison - {now}.csv"
        )
    )
    return test2_infos, test2_score
