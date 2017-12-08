# # -*- coding: utf-8 -*-
import re


def clean_html(raw_html):
    """Remove HTML tags from scrapped HTML."""
    regex = re.compile(u'<.*?>')
    clean_text = re.sub(regex, '', raw_html)
    return clean_text


# def convert(filename):
#     text = textract.process(
#         filename,
#         encoding='utf-8',
#     )
#     if not text:
#         text = textract.process(
#             filename,
#             encoding='utf-8',
#             method='tesseract',
#             language='en'
#         )
#     return text.decode('utf-8')
#
#
# def grab_references(text_pdf, keyword):
#     references = ''
#     status = ''
#     # Ensure we match one and only one section
#     status += '[+]Extract Section :'
#     # Multiple results. Uses a regex to exclude the table of content
#     # If their is multiple results, split the text
#     regex = r"\n+" + keyword + "s?[:.]?(?=[\n]+)"
#     end_indexes = [
#          m.end() for m in re.finditer(
#                regex,
#                text_pdf,
#                re.DOTALL | re.IGNORECASE
#            )
#      ]
#     if not end_indexes:
#         return None
#
#     if len(end_indexes) == 1:
#         status += '1'
#         # If their is exactly one occurence, we take the first
#         section_index = end_indexes[0]
#         text_sections = [text_pdf[section_index:]]
#     else:
#         status += 'x'
#         # Else we split the text into sections
#         prev = 0
#         text_sections = []
#         for index in end_indexes:
#             text_sections.append(text_pdf[prev:index - len(keyword)])
#             prev = index
#
#     for text_section in text_sections:
#         # regex = r"[\n]+[ ]{2,}references *\n*(.*?)(?=\n{2,}|($))"
#         regex = r'(\n\d+\.{1}\n+)(.*?)(?=\n{2,}|($))'
#         matches = re.finditer(regex, text_section, re.DOTALL | re.IGNORECASE)
#         for num, match in enumerate(matches):
#             references += match.group()
#     print(status)
#     return references
#
#
# def grab_keyword(text_pdf, keyword):
#     result = []
#     regex = r'\. *([^\.]*' + keyword + '[^\.]*\.*)'
#     matches = re.finditer(regex, text_pdf, re.IGNORECASE)
#     for num, match in enumerate(matches):
#         result.append(match.group(1))
#
#     return result
