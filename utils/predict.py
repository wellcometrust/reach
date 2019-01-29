import pandas as pd
from functools import partial
from settings import settings
from multiprocessing import Pool

logger = settings.logger


def decide_components(single_reference):
    """With the predicted components of one reference, decide which of
    these should be used for each component i.e. if there are multiple
    authors predicted and they arent next to each other, then decide which
    one to use.
    """

    # Add a block number, this groups neighbouring predictions of
    # the same type together.
    block_number = pd.DataFrame({
        'Block': (
            single_reference[
                "Predicted Category"
            ].shift(1) != single_reference[
                "Predicted Category"
            ]).astype(int).cumsum()
    })
    single_reference = pd.concat([single_reference, block_number], axis=1)
    single_reference_components = {}

    for classes in set(single_reference["Predicted Category"]):

        # Are there any sentences of this type (i.e. Authors, Title)?
        classornot = sum(single_reference['Predicted Category'] == classes)

        if classornot != 0:

            # Find how many blocks there are of this class type
            number_blocks = len(
                single_reference['Block'][single_reference[
                    'Predicted Category'
                ] == classes].unique()
            )

            if number_blocks == 1:
                # Just record this block separated by commas
                single_reference_components.update({
                    classes: ", ".join(
                        single_reference[
                            'Reference component'
                        ][single_reference[
                            'Predicted Category'
                        ] == classes]
                    )
                })
            else:
                # Pick the block containing the highest probability
                # argmax takes the first argument anyway (so if there are 2
                # of the same probabilities it takes the first one)
                # could decide to do this randomly with argmax.choice()
                # (random choice)
                
                highest_probability_index = single_reference[
                    single_reference['Predicted Category'] == classes
                ]['Prediction Probability'].idxmax()

                highest_probability_block = single_reference[
                    'Block'
                ][highest_probability_index]

                # Use everything in this block, separated by comma
                single_reference_components.update({
                    classes: ", ".join(
                        single_reference[
                            "Reference component"
                        ][single_reference[
                            'Block'
                        ] == highest_probability_block]
                    )
                })
        else:
            # There are none of this classification, append with blank
            single_reference_components.update({classes: ""})

    return single_reference_components


def single_reference_structure(components_single_reference,
                               prediction_probability_threshold):
    """Predict the structure for a single reference given all
    the components predicted for it.
    """
    # Delete all the rows which have a probability <0.75
    components_single_reference = components_single_reference[
        components_single_reference[
            'Prediction Probability'
        ].astype(float) > prediction_probability_threshold
    ]

    # Decide the best options for each reference component, resulting
    # in one structured reference
    single_reference = pd.DataFrame(
        decide_components(components_single_reference),
        index=[0]
    )

    return single_reference


def _get_structure(reference_id, document):
    # The components and predictions for one document one reference

    components_single_reference = document.loc[
        document['Reference id'] == reference_id
    ].reset_index()

    # Structure:
    single_reference = single_reference_structure(
        components_single_reference,
        settings.PREDICTION_PROBABILITY_THRESHOLD
    )

    if len(single_reference) != 0:

        # Only if there were some enteries for this reference with
        # high prediction probabilies
        single_reference[
            "Document id"
        ] = components_single_reference['Document id'][0]

        single_reference[
            "Reference id"
        ] = components_single_reference['Reference id'][0]

        single_reference[
            "Document uri"
        ] = components_single_reference['Document uri'][0]

    return pd.DataFrame.from_dict(single_reference)


def predict_structure(reference_components_predictions,
                      prediction_probability_threshold,
                      num_workers=None):
    """Predict the structured references for all the references. Go through
    each reference for each document in turn.
    """

    # Convert to pd dataframe, although when this function is refactored we shouldnt have to do this
    reference_components_predictions = pd.DataFrame.from_dict(reference_components_predictions)

    all_structured_references = []
    document_ids = set(reference_components_predictions['Document id'])

    logger.info(
        "[+] Predicting structure of references from %s  documents...",
        str(len(document_ids))
    )
    if num_workers == 1:
        pool_map = map
    else:
        pool = Pool(num_workers)
        pool_map = pool.map
        logger.info(
            '[+] Using pooled predictor with %s workers',
            pool._processes
        )
    for document_id in document_ids:
        document = reference_components_predictions.loc[
            reference_components_predictions['Document id'] == document_id
        ]

        reference_ids = set(document['Reference id'])

        # doc_references = map(
        #     lambda x: _get_structure(x, document),
        #     reference_ids
        # )
        doc_references = pool_map(
            partial(_get_structure,
                    document=document),
            reference_ids
        )
        all_structured_references.extend(
            doc_references
        )

    all_structured_references = pd.concat(
        all_structured_references,
        axis=0,
        ignore_index=True,
        sort=False
    )

    logger.info("[+] Reference structure predicted")
    return all_structured_references


def predict_reference_comp(mnb, vectorizer, word_list):
    # To test what individual things predict,
    # it can deal with a list input or not
    # The maximum probability found is the probability
    # of the predicted classification

    vec_list = vectorizer.transform(word_list).toarray()
    predict_component = mnb.predict(vec_list)
    predict_component_probas = mnb.predict_proba(vec_list)
    predict_component_proba = [
        single_predict.max() for single_predict in predict_component_probas
    ]

    return predict_component[0], predict_component_proba[0]

def is_year(component):
    valid_years_range = range(1800, 2020)
    return (
                (
                    component.isdecimal()
                    and int(component) in valid_years_range
                )
                or
                (
                    len(component) == 6
                    and component[1:5].isdecimal()
                    and int(component[1:5]) in valid_years_range
                )
            )
        

def _get_component(component, mnb, vectorizer):

    if is_year(component):
        pred_cat = 'PubYear'
        pred_prob = 1
    else:
        pred_cat, pred_prob = predict_reference_comp(
            mnb,
            vectorizer,
            [component]
        )

    return {
            'Predicted Category': pred_cat,
            'Prediction Probability': pred_prob
            }

def predict_references(mnb,
                       vectorizer,
                       reference_components,
                       num_workers=None):

    """
    Predicts the categories for a list of reference components.
    Input:
    - mnb: The trained multinomial naive Bayes model for predicting the categories of reference components
    - vectorizer: The vector of word counts in the training set
    - reference_components: A list of reference components
    - num_workers: How many different processors you want to use in multiprocessing the predicting
    Output:
    - A list of dicts [{"Predicted Category": , "Prediction Probability": } ...]
    """

    logger.info(
        "[+] Predicting the categories of %s  reference components ...",
        str(len(reference_components))
    )
    predict_all = []

    # The model cant deal with predicting so many all at once,
    # so predict in a loop
    if num_workers == 1:
        pool_map = map
    else:
        pool = Pool(num_workers)
        pool_map = pool.map
        logger.info(
            '[+] Using pooled predictor with %s workers',
            pool._processes
        )

    predict_all = list(pool_map(
        partial(_get_component,
                mnb=mnb,
                vectorizer=vectorizer),
        reference_components
    ))

    logger.info("Predictions complete")

    return predict_all

