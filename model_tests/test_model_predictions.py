from .tests_utils import test_model
from utils import FileManager
from .test_settings import settings


def test_model_predictions(publications):
    """TEST 1 : Model predictions
    How well does the model predict components?
    """

    logger = settings.logger
    fm = FileManager()

    mnb = fm.get_file(
        settings.CLASSIFIER_FILENAME,
        settings.MODEL_DIR,
        'pickle'
    )
    vectorizer = fm.get_file(
        settings.VECTORIZER_FILENAME,
        settings.MODEL_DIR,
        'pickle'
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
