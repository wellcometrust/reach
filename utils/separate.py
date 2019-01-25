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


def process_reference_section(doc, regex):
    """Converts the unstructured text into reference components
    Input:
    - a SectionedDocument tuple
    Output:
    - A list of references data which come into a dict with keys
        about the reference string, reference id, document uri and
        document id
    Nomenclature:
    Document > References
    """

    logger.info(
        "Processing unstructured references into reference components ... "
    )

    assert doc.section, "document section is empty"

    # e.g.
    # Document 1:
    # \n1.\n Smith, et al, 2000 \n2.\n Jones, 1998
    # Document 2:
    # Eric, 1987

    references_data = []
    references = split_sections(doc.section, regex)
    for reference in references:
        references_data.append({
            'Reference': reference,
            'Reference id': hash(reference),
            # TODO: remove these
            'Document uri': doc.uri,
            'Document id': doc.id,
        })
    return references_data
