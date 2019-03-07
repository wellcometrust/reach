from settings import settings

logger = settings.logger


def split_reference(reference):
    """Split up one individual reference into reference components.
    Each component is numbered by the reference it came from.
    """
    if not reference:
        return []

    components = []

    # I need to divide each reference by the full stops
    # AND commas and categorise
    reference_sentences_mid = [
        # Notice that we remove spaces for elem
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


def merge_components(reference_components):
    """With the predicted components of one reference, decide which of
    these should be used for each component i.e. if there are multiple
    authors predicted and they arent next to each other, then decide which
    one to use.
    """
    if not reference_components:
        return []

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


def is_year(component):
    valid_years_range = range(1800, 2020)
    if len(component) == 6:
        component = component[1:5]
    return component.isdecimal() and int(component) in valid_years_range


def predict_components(model, reference_components):

    """
    Predicts the categories for a list of reference components.
    Input:
    - model: The trained multinomial naive Bayes model for predicting the categories of reference components
    - reference_components: A list of reference components
    Output:
    - A list of dicts [{"Predicted Category": , "Prediction Probability": } ...]
    """

    # logger.info(
    #     "[+] Predicting the categories of %s  reference components ...",
    #     str(len(reference_components))
    # )
    if not reference_components:
        return []

    component_predictions = model.predict(reference_components)
    component_predictions_probs = [
        p.max() for p in model.predict_proba(reference_components)
    ]
    
    predicted_components = []
    for i, component in enumerate(reference_components):
        if is_year(component):
            cat = 'PubYear'
            prob = 1
        else:
            cat = component_predictions[i]
            prob = component_predictions_probs[i]

        predicted_components.append({
            'Reference component': component,
            'Predicted Category': cat,
            'Prediction Probability': prob
        })

    # logger.info("Predictions complete")
    return predicted_components


def structure_reference(model, reference):
    splitted_components = split_reference(reference)

    predicted_components = predict_components(
        model,
        splitted_components
    )

    structured_reference = merge_components(predicted_components)
    
    return structured_reference
