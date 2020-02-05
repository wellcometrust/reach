# -*- coding: utf-8 -*-

import re

from reference_splitter import split_section

# def split_section(references_section, regex="\n"):
#     """Converts the unstructured text into reference components
#     Input:
#     - a References section string
#     Output:
#     - A list of references data which come into a dict with keys
#         about the reference string, reference id, document uri and
#         document id
#     Nomenclature:
#     Document > References
#     """
#     references = re.split(regex, references_section)
#     # Remove any row with less than 10 characters in
#     # (these can't be references)
#     references = [r for r in references if len(r) > 10]
#     # delete '-\n', convert \n to spaces, convert â€™ to ', convert â€“ to -
#     references = [
#         reference.replace(
#             "-\n", ""
#         ).replace(
#             "\n", " "
#         ).replace(
#             "â€™", "'"
#         ).replace(
#             "â€“", "-"
#         )
#         for reference in references
#     ]

#     return references
