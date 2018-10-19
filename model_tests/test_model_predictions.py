from .tests_utils import test_model
from utils import load_pickle_file
from .test_settings import settings


def test_model_predictions(publications):
    """TEST 1 : Model predictions
    How well does the model predict components?
    """

    logger = settings.logger

    mnb = load_pickle_file(settings.MODEL_DIR, settings.CLASSIFIER_FILENAME)
    vectorizer = load_pickle_file(
        settings.MODEL_DIR,
        settings.VECTORIZER_FILENAME
    )

    logger.info("============")
    logger.info("Test 1 - How well does the model predict components?")
    logger.info("============")
    publications_to_test_model =\
        publications.ix[:(settings.TEST_SET_SIZE - 1), :]

    num_mislabeled, len_test_set, prop_cats_correct_label = test_model(
        mnb, vectorizer, publications_to_test_model)

    test1_info = str(
        "Number of correctly labelled test points " +
        str(len_test_set-num_mislabeled) + " out of " +
        str(len_test_set) + " = " +
        str(round(100*(len_test_set-num_mislabeled)/len_test_set)) + "%\n" +
        "By category:\n" +
        str(prop_cats_correct_label))

    logger.info(test1_info)

    test1_score = (len_test_set-num_mislabeled) / len_test_set

    return test1_info, test1_score
