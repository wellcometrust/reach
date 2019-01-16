# -*- coding: utf-8 -*-

import re

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
