# -*- coding: utf-8 -*-

import re

import numpy as np
import pandas as pd
from settings import settings

logger = settings.logger


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

def process_reference_section(sections_data, regex):
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

    logger.info(
        "Processing unstructured references into reference components ... "
    )

    # assert 'sections' in raw_text_data, "raw_text_data.sections not defined"

    # e.g.
    # Document 1:
    # \n1.\n Smith, et al, 2000 \n2.\n Jones, 1998
    # Document 2:
    # Eric, 1987

    references_data = []
    for section in sections_data:

        references = split_sections(section['Section'], regex)
        for reference in references:
            references_data.append({
                'Reference': reference,
                'Reference id': hash(reference),
                'Document uri': section['Document uri'],
                'Document id': section['Document id']
            })

    return references_data

def summarise_predicted_references(reference_components, raw_text_data):
    """Get the number of references and information for each document."""

    logger.info("Number of references for each document being found ... ")
    assert 'sections' in raw_text_data, "raw_text_data.sections not defined"

    #####
    # 1. Get some sumamry reference information about each document
    #####

    all_document_info = pd.DataFrame(
        raw_text_data[['pdf', 'title', 'uri', 'year']]
    )
    all_document_info['Document'] = range(0, len(raw_text_data))

    predicted_number_refs_temp = []

    for document_number in set(all_document_info):
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

    logger.info("Number of JSON with reference section is %s", str(count_ref))
    logger.info("Number of JSON is %s", str(len(raw_text_data)))
    logger.info(
        "Average number of references predicted %s",
        str(round(np.mean(
            predicted_number_refs['Predicted number of references']
        )))
    )

    return predicted_number_refs


def save_reference_components(reference_components):
    logger.info("Saving reference components ... ")
    reference_components.to_csv('reference_components.csv', index=False)


def save_predicted_number_refs(predicted_number_refs):
    logger.info("Saving predicted number of references ... ")
    predicted_number_refs.to_csv('predicted_number_refs.csv', index=False)
