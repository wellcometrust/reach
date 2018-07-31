import re
import json
import random
import pickle

import numpy as np
import pandas as pd


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


def split_sections(references_section, regex="\n"):
    """
    Split up a raw text reference section into individual references
    """
    references = re.split(regex, references_section)
    # Remove any row with less than 10 characters in
    # (these can't be references)
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
        )
        for elem in references
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

    """
    print("Processing unstructured references into reference components ... ")

    assert 'sections' in raw_text_data, "raw_text_data.sections not defined"

    # e.g.
    # Document 1:
    # \n1.\n Smith, et al, 2000 \n2.\n Jones, 1998
    # Document 2:
    # Eric, 1987

    raw_reference_components = []

    for _, document in raw_text_data.iterrows():
        if document["sections"]:

            # Get all the references text for this WHO document and split it
            # up into individual references
            references_section = document['sections']['Reference']
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


def summarise_predicted_references(reference_components, raw_text_data):
    """Get the number of references and information for each document."""

    print("Number of references for each document being found ... ")
    assert 'sections' in raw_text_data, "raw_text_data.sections not defined"

    #####
    # 1. Get some sumamry reference information about each document
    #####

    all_document_info = pd.DataFrame(
        raw_text_data[['pdf', 'title', 'uri', 'year']]
    )
    all_document_info['Document'] = range(0, len(raw_text_data))

    _s = reference_components['Document number']

    predicted_number_refs_temp = []

    for document_number in set(document_numbers):
        document_references = reference_components.loc[
            reference_components[
                'Document number'
            ] == document_number]['Reference number'].unique()
        predicted_number_refs_temp.append(
            [document_number, len(document_references)]
        )

    predicted_number_refs = pd.DataFrame(
        predicted_number_refs_temp,
        columns=['Document', 'Predicted number of references']
    )
    predicted_number_refs = predicted_number_refs.join(
        all_document_info.set_index('Document'),
        on='Document'
    )

    #####
    # 2. Get the number of pdfs which have data in the references
    #    section part of the JSON
    #####

    count_ref = len([i for i in raw_text_data["sections"] if i])

    json_details = {"Number of JSON with reference section": count_ref}
    print("Number of JSON with reference section is ", str(count_ref))
    print("Number of JSON is ", str(len(raw_text_data)))
    print(
        "Average number of references predicted ",
        str(round(np.mean(
            predicted_number_refs['Predicted number of references']
        )))
    )

    return predicted_number_refs


def test_get_reference_components(predicted_number_refs, actual_number_refs):
    """
    Input:
    - How many references found in each document
    - How many references there actually were in a sample of documents

    Output:
    - How much these values match for the sample manually counted
    - This is measured as the average difference as a proportion of the actual
      number
    - The comparison numbers
    """

    print("How well the number of references are predicted being computed...")
    comparison = []
    for index, row in actual_number_refs.iterrows():

        # This will happen when there was a references section pulled only
        # There are a few in the sample who had no references section pulled

        this_document_predicted = predicted_number_refs.loc[
            predicted_number_refs['uri'] == row['uri']
        ].reset_index()

        if (len(this_document_predicted) == 0):
            this_document_predicted = None
            difference_per = None
        else:
            this_document_predicted = this_document_predicted[
                'Predicted number of references'
            ][0]

            if (row['Number of References in WHO pdf'] == 0):
                difference_per = None
            else:
                difference_per = abs(
                    row['Number of References in WHO pdf']
                    - this_document_predicted
                ) / row['Number of References in WHO pdf']

        comparison.append(
            [row['Number of References in WHO pdf'],
             this_document_predicted, difference_per]
        )

    comparison = pd.DataFrame(
        comparison,
        columns=[
            "Number of References in WHO pdf",
            "Predicted number of references",
            "Difference as proportion of actual number"
        ]
    )

    mean_difference_per = np.mean(
        comparison["Difference as proportion of actual number"]
    )

    print(
        "Average difference between actual and predicted number of references",
        "as proportion of actual number is ",
        str(round(mean_difference_per, 4))
    )

    return mean_difference_per, comparison


def save_reference_components(reference_components):
    print("Saving reference components ... ")
    reference_components.to_csv('reference_components.csv', index=False)


def save_predicted_number_refs(predicted_number_refs):
    print("Saving predicted number of references ... ")
    predicted_number_refs.to_csv('predicted_number_refs.csv', index=False)
