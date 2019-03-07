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


def split_references(references):
    raw_reference_components = []
    for reference in references:
        # Get the components for this reference and store
        components = split_reference(reference['Reference'])

        for component in components:
            raw_reference_components.append({
                'Reference component': component,
                'Reference id': reference['Reference id']
            })

    logger.info("Reference components found")
    return raw_reference_components


def decide_components(reference_components):
    """With the predicted components of one reference, decide which of
    these should be used for each component i.e. if there are multiple
    authors predicted and they arent next to each other, then decide which
    one to use.
    """
    
    # Add a group number for components that are next to components
    #   with same category. For example title next to a title.
    group_index = 1
    for i, comp in enumerate(reference_components[:-1]):
        comp['Group'] = group_index
        next_comp = reference_components[i+1]
        if next_comp['Predicted Category'] != comp['Predicted Category']:
            group_index += 1
    reference_components[-1]['Group'] = group_index
    
    structured_reference = {}
    categories =  settings.REF_CLASSES
    for category in categories:

        merged_component = ""

        category_components = [
            comp for comp in reference_components
            if comp['Predicted Category']==category
        ]
        if category_components:
            max_prob_component = max(category_components, key=lambda x: x['Prediction Probability'])
            max_prob_group = max_prob_component['Group']

            group_components = [
                comp for comp in category_components
                if comp['Group'] == max_prob_group
            ]
            merged_component = ", ".join([
                comp['Reference component'] for comp in group_components
            ])
            
        structured_reference.update({category: merged_component})

    return structured_reference


def merge_components(pool_map, predicted_components):
    """
    Predict the structured references for all the references of
    one document.
    """
    reference_ids = list(set([
        comp['Reference id'] for comp in predicted_components]
    ))

    # We group components by reference before merging
    references_components = [
        [
            comp for comp in predicted_components 
            if comp['Reference id']==reference_id
        ]
        for reference_id in reference_ids
    ]

    merged_components = pool_map(
        decide_components,
        references_components
    )

    for i, reference_components in enumerate(merged_components):
        reference_components.update({
            'Reference id': reference_ids[i]
        })

    logger.info("[+] Reference structure predicted")
    return merged_components


def _predict_component(model, word_list):
    # To test what individual things predict,
    # it can deal with a list input or not
    # The maximum probability found is the probability
    # of the predicted classification

    component_prediction = model.predict(word_list)
    component_prediction_probabilities = model.predict_proba(word_list)
    component_prediction_probability = [
        p.max() for p in component_prediction_probabilities
    ]

    return component_prediction[0], component_prediction_probability[0]


def is_year(component):
    valid_years_range = range(1800, 2020)
    if len(component) == 6:
        component = component[1:5]
    return component.isdecimal() and int(component) in valid_years_range


def predict_component(component, model):

    if is_year(component):
        pred_cat = 'PubYear'
        pred_prob = 1
    else:
        pred_cat, pred_prob = _predict_component(
            model,
            [component]
        )

    return {
        'Predicted Category': pred_cat,
        'Prediction Probability': pred_prob
    }

def predict_components(pool_map, model, reference_components):

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

    predictions = list(pool_map(
        partial(predict_component,
                model=model),
        [comp['Reference component'] for comp in reference_components]
    ))

    predicted_components = []
    for i, predicted_component in enumerate(predictions):
        predicted_components.append({
            'Reference id': reference_components[i]['Reference id'],
            'Reference component': reference_components[i]['Reference component'],
            'Predicted Category': predicted_component['Predicted Category'],
            'Prediction Probability': predicted_component['Prediction Probability']
        })

    logger.info("Predictions complete")

    return predicted_components


def structure_references(pool_map, model, splitted_references):
    splitted_components = split_references(splitted_references)

    # TO DO: Rather than just skip,
    # return empty lists in predict_references, predict_structure and fuzzy_match_blocks
    if len(splitted_components) == 0:
        return []

    predicted_components = predict_components(
        pool_map,
        model,
        splitted_components
    )

    structured_references = merge_components(
        pool_map,
        predicted_components
    )
    
    return structured_references
