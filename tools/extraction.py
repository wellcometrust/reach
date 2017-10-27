import textract
import re


def cleanhtml(raw_html):
    # Remove HTML tags from scrapped HTML
    cleanr = re.compile(u'<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext


def convert(filename):
    text = textract.process(filename, encoding='utf-8')
    if not text:
        text = textract.process(filename, encoding='utf-8', method='tesseract')

    return text.decode('utf-8')


def grab_references(text_pdf, keyword):
    references = ''
    # Ensure we only match a reference list
    ref_index = text_pdf.lower().find(keyword)
    text_pdf = text_pdf[ref_index:]
    # regex = r"[\n]+[ ]{2,}references *\n*(.*?)(?=\n{2,}|($))"
    regex = r'(\n\d+\.{1}\n+)(.*?)(?=\n{2,}|($))'
    matches = re.finditer(regex, text_pdf, re.DOTALL | re.IGNORECASE)
    for num, match in enumerate(matches):
        references += match.group()

    return references


def grab_keyword(text_pdf, keyword):
    result = []
    regex = r'\. *([^\.]*' + keyword + '[^\.]*\.*)'
    matches = re.finditer(regex, text_pdf, re.IGNORECASE)
    for num, match in enumerate(matches):
        result.append(match.group(1))

    return result
