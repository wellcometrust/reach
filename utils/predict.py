import pandas as pd
from functools import partial
from settings import settings

logger = settings.logger


def split_reference(reference):
    """Split up one individual reference into reference components.
    Each component is numbered by the reference it came from.
    """
    components = []

    # I need to divide each reference by the full stops
    # AND commas and categorise
    reference_sentences_mid = [
        elem.strip()
        for elem in reference.replace(
            ',', '.'
        ).replace(
            '?', '?.'
        ).replace(
            '!', '!.'
        ).split(".")
    ]

    for ref in reference_sentences_mid:
        if ref:
            components.append(ref)

    return components


def process_references(references):
    raw_reference_components = []
    for reference in references:
        # Get the components for this reference and store
        components = split_reference(reference['Reference'])

        for component in components:
            raw_reference_components.append({
                'Reference component': component,
                'Reference id': reference['Reference id'],
                'Document uri': reference['Document uri'],
                'Document id': reference['Document id']
            })

    logger.info("Reference components found")
    return raw_reference_components


def decide_components(single_reference):
    """With the predicted components of one reference, decide which of
    these should be used for each component i.e. if there are multiple
    authors predicted and they arent next to each other, then decide which
    one to use.
    """
    single_reference = pd.DataFrame(single_reference)

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

    categories =  settings.REF_CLASSES
    for category in categories:

        cat = ""
        category_exists = category in single_reference['Predicted Category'].tolist()
        if category_exists:
            # Pick the block containing the highest probability
            # argmax takes the first argument anyway (so if there are 2
            # of the same probabilities it takes the first one)
            # could decide to do this randomly with argmax.choice()
            # (random choice)

            highest_probability_index = single_reference[
                single_reference['Predicted Category'] == category
            ]['Prediction Probability'].idxmax()

            highest_probability_block = single_reference[
                'Block'
            ][highest_probability_index]

            cat = ", ".join(
                    single_reference[
                        "Reference component"
                    ][single_reference[
                        'Block'
                    ] == highest_probability_block]
                )
            
        single_reference_components.update({category: cat})

    return single_reference_components


def predict_structure(pool_map, reference_components_predictions,
                      prediction_probability_threshold):
    """
    Predict the structured references for all the references of
    one document.
    """
    reference_ids = list(set([c['Reference id'] for c in reference_components_predictions]))

    document_components_list = [
        [c for c in reference_components_predictions if c['Reference id']==reference_id]
        for reference_id in reference_ids
    ]

    doc_references = pool_map(
        decide_components,
        document_components_list
    )
    
    document_id = reference_components_predictions[0]['Document id']
    document_uri = reference_components_predictions[0]['Document uri']
    for i, ref in enumerate(doc_references):
        ref.update({
            'Document id': document_id,
            'Document uri': document_uri,
            'Reference id': reference_ids[i]
        })

    logger.info("[+] Reference structure predicted")
    return pd.DataFrame(doc_references)


def predict_reference_comp(model, word_list):
    # To test what individual things predict,
    # it can deal with a list input or not
    # The maximum probability found is the probability
    # of the predicted classification

    predict_component = model.predict(word_list)
    predict_component_probas = model.predict_proba(word_list)
    predict_component_proba = [
        single_predict.max() for single_predict in predict_component_probas
    ]

    return predict_component[0], predict_component_proba[0]


def is_year(component):
    valid_years_range = range(1800, 2020)
    if len(component) == 6:
        component = component[1:5]
    return component.isdecimal() and int(component) in valid_years_range


def _get_component(component, model):

    if is_year(component):
        pred_cat = 'PubYear'
        pred_prob = 1
    else:
        pred_cat, pred_prob = predict_reference_comp(
            model,
            [component]
        )

    return {
            'Predicted Category': pred_cat,
            'Prediction Probability': pred_prob
            }

def predict_references(pool_map, model,
                       reference_components):

    """
    Predicts the categories for a list of reference components.
    Input:
    - pool_map: Pool map used for multiprocessing the predicting
    - model: The trained multinomial naive Bayes model for predicting the categories of reference components
    - reference_components: A list of reference components
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

    predict_all = list(pool_map(
        partial(_get_component,
                model=model),
        reference_components
    ))

    logger.info("Predictions complete")

    return predict_all


def structure_references(pool_map, model, splitted_references):
    # Split references into components
    splitted_components = process_references(splitted_references)

    # TO DO: Rather than just skip,
    # return empty lists in predict_references, predict_structure and fuzzy_match_blocks
    if len(splitted_components) == 0:
        return []

    # Predict the references types (eg title/author...)
    # logger.info('[+] Predicting the reference components')
    components_predictions = predict_references(
        pool_map,
        model,
        [c['Reference component'] for c in splitted_components]
    )

    # Link predictions back with all original data (Document id etc)
    # When we merge and splitted_components is a dict not a dataframe then
    # we could just merge the list of dicts
    reference_components_predictions = splitted_components
    for i, d in enumerate(components_predictions):
        reference_components_predictions[i].update({
            'Predicted Category': d['Predicted Category'],
            'Prediction Probability': d['Prediction Probability']
        })

    # Predict the reference structure
    predicted_reference_structures = predict_structure(
        pool_map,
        reference_components_predictions,
        settings.PREDICTION_PROBABILITY_THRESHOLD
    )
    return predicted_reference_structures
