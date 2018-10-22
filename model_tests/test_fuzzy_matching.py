import pandas as pd
from datetime import datetime
from .test_settings import settings
from .tests_utils import test_match


def test_fuzzy_matching(match_publications, test_publications):
    """ TEST 4 : Fuzzy matching of references
    How well the algo matches list references with WT references.
    """
    now = datetime.now()
    logger = settings.logger

    logger.info("============")
    logger.info(
        "Test 4 - How well the algo matches list references with WT references"
    )
    logger.info("===========")

    # Take the negative examples out of the match publications:
    neg_test_pub_ids = test_publications.loc[
        test_publications['Type'] == 'Negative'
    ]['Match pub id']

    match_publications = match_publications.loc[
        ~match_publications['uber_id'].isin(neg_test_pub_ids)
    ].reset_index()

    (true_positives, true_negatives,
     false_negatives, false_positives) = test_match(
        match_publications,
        test_publications,
        settings.FUZZYMATCH_THRESHOLD,
        settings.BLOCKSIZE
    )

    num_pos = sum(test_publications['Type'] == 'Positive')
    num_neg = sum(test_publications['Type'] == 'Negative')

    proportion_correct_match = (
        len(true_positives) + (num_neg - len(false_negatives))
    )/(num_pos + num_neg)

    test4_info = """Proportion correctly matched from a random sample of
    {pos} positive and {neg} negative samples: {correct}
    Number from positive set with a match with the same ID: {true_pos}
    Number from positive set with a match with a different ID: {true_neg}
    Number from negative set with a match with a different ID: {false_pos}
    Number from negative set with a match with the same ID: {false_neg}
    Number from negative set with no matches: {no_match}
    """.format(
        pos=num_pos,
        neg=num_neg,
        correct=proportion_correct_match,
        true_pos=len(true_positives),
        true_neg=len(false_negatives),
        false_pos=len(false_positives),
        false_neg=len(false_positives),
        no_match=num_neg - len(false_negatives) - len(false_positives),
    )

    true_negatives['Type'] = "Positive set with match with a different ID"
    false_negatives['Type'] = "Negative set with a match"

    logger.info(test4_info)

    pd.concat([true_negatives, false_negatives]).to_csv(
        f"{settings.LOG_FILE_PREFIX}/Test results - False matches - {now}.csv")

    test4_score = proportion_correct_match
    return test4_info, test4_score
