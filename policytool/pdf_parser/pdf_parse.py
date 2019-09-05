import errno
import logging
import math
import os
import subprocess
import tempfile

from bs4 import BeautifulSoup as bs

from .objects.PdfObjects import PdfFile, PdfPage, PdfLine
from .tools.extraction import _find_elements

BASE_FONT_SIZE = -10


def parse_pdf_document(document):
    """ Parses a file using pdftotext, returning a
    PdfFile object, easier to analyse.

    Args:
        document: file object, pointing to a named file
    """

    logger = logging.getLogger(__name__)
    with tempfile.NamedTemporaryFile(suffix='.xml', mode='w+b') as tf:
        # Run pdftohtml on the document, and output an xml formated document
        cmd = [
            'pdftohtml',
            '-i',
            '-xml',
            '-zoom',
            '1.5',
            document.name,
            tf.name
        ]

        try:
            subprocess.check_call(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except subprocess.CalledProcessError as e:
            logger.warning(
                "The pdf [%s] could not be converted: %r",
                document.name,
                e.stderr,
            )
            return None, None

        try:
            # Try to get file stats in order to check both its existence
            # and if it has some content
            st = os.stat(tf.name)
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise
            logger.warning('Error trying to open the parsed file: %s', e)
            return None, None

        if st.st_size == 0:
            logger.warning(
                'Error trying to open the parsed file: The file is empty'
            )
            return None, None

        soup = bs(tf.read(), 'html.parser')

        file_pages = []
        pages = soup.find_all('page')
        full_text = soup.text

        for num, page in enumerate(pages):
            words = page.find_all('text')

            page_lines = []
            pdf_line = None
            if words:
                pos_y = words[0].attrs['top']
                cur_line = ''
                font_size = float(words[0].attrs['height'])
                for word in words:
                    cur_font_size = float(word.attrs['height'])
                    if word.attrs['top'] == pos_y and font_size == cur_font_size:
                        if word.string:
                            cur_line = cur_line + ' ' + word.string
                    else:
                        pdf_line = PdfLine(
                            int(math.ceil(font_size)),
                            False,
                            cur_line, num,
                            '',
                        )
                        if pdf_line:
                            page_lines.append(pdf_line)
                        cur_line = word.string if word.string else ''
                        pos_y = word.attrs['top']
                        font_size = cur_font_size
                if pdf_line:
                    page_lines.append(pdf_line)
            file_pages.append(PdfPage(page_lines, num))

        pdf_file = PdfFile(file_pages)
        return pdf_file, full_text


def grab_section(pdf_file, keyword):
    """Given a pdf parsed file object (PdfFile) and a keyword corresponding to
    a title, returns the matching section of the pdf text.
    """
    result = ''
    text = ''
    elements = _find_elements(pdf_file, keyword)
    for start_title, end_title in elements:
        if not end_title:
            end_page = len(pdf_file.pages)
        else:
            end_page = end_title.page_number + 1
        for page_number in range(start_title.page_number, end_page):
            if pdf_file.get_page(page_number).get_page_text(True):
                text += pdf_file.get_page(page_number).get_page_text()
        if end_title and (start_title.page_number != end_title.page_number):
            result += text[
                text.find(start_title.text):text.find(end_title.text)
            ]
        else:
            result += text[text.find(start_title.text):]
        text = ''
    return result
