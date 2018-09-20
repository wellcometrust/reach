import re
import pandas as pd


def split_reference(reference):
    """Split up one individual reference into reference components
    Each component is numbered by the reference it came from
    """

    components = []

    # Split by full stop AND commas and get rid of
    # whitespaces from beginning and end
    reference_sentences_mid = [
        elem.strip() for elem in reference.replace(
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


def split_sections(references_section, regex="\n"):
    '''
    Split up a raw text reference section into individual references
    '''
    references = re.split(regex, references_section)
    # Remove any row with less than 10 characters in (can't be references)
    references = [k for k in references if len(k) > 10]
    # delete '-\n', convert \n to spaces, convert â€™ to ', convert â€“ to -
    references = [
        elem.replace(
            "-\n", ""
        ).replace(
            "\n", " "
        ).replace(
            "â€™", "'"
        ).replace(
            "â€“", "-"
        ) for elem in references
    ]

    return references


def process_reference_section(raw_text_data, regex):
    """Converts the unstructured text into reference components

    Input:
    - The unstructured references (e.g. from WHO)

    Output:
    - A list of reference components from these
    - The number of references for each document
    - Meta info for each document index

    Nomenclature:
    Document > Reference > Reference components

    e.g.
    Document 1:
    \n1.\n Smith, et al, 2000 \n2.\n Jones, 1998
    Document 2:
    Eric, 1987

    'Reference component': The list of reference components
    ['Smith', 'et al', '2000', 'Jones', '1998', 'Eric', '1987']
    """

    print("Processing unstructured references into reference components ... ")

    assert 'sections' in raw_text_data, "raw_text_data.sections not defined"

    raw_reference_components = []

    for _, document in raw_text_data.iterrows():
        if document["sections"]:

            references_section = document["sections"]['Reference']
            references = split_sections(references_section, regex)

            for reference in references:
                # Get the components for this reference and store
                components = split_reference(reference)

                for component in components:
                    raw_reference_components.append({
                        'Reference component': component,
                        'Reference id': hash(reference),
                        'Document uri': document['uri'],
                        'Document id': document['hash']
                    })

    reference_components = pd.DataFrame(raw_reference_components)

    print("Reference components found")

    return reference_components


def save_reference_components(reference_components):
    print("Saving reference components ... ")
    reference_components.to_csv('reference_components.csv', index=False)
