import math
import os
import subprocess
import logging
from bs4 import BeautifulSoup as bs
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from .objects.PdfObjects import PdfFile, PdfPage, PdfLine
from .tools.extraction import _find_elements
from pdfminer.layout import (LAParams, LTTextBox, LTTextLine, LTChar, LTAnno,
                             LTTextBoxHorizontal, LTTextLineHorizontal)

BASE_FONT_SIZE = -10


TEXT_ELEMENTS = [
    LTTextBox,
    LTTextBoxHorizontal,
    LTTextLine,
    LTTextLineHorizontal
]


class PDFTextPageAggregator(PDFPageAggregator):
    """As we don't need schemas and pictures, just don't render them."""

    def render_image(self, name, stream):
        return

    def paint_path(self, gstate, stroke, fill, evenodd, path):
        return


def get_line_infos(txt_obj):
    if isinstance(txt_obj, LTChar):
        if 'bold' in txt_obj.fontname.lower():
            return txt_obj.size, True, txt_obj.fontname
        else:
            return txt_obj.size, False, txt_obj.fontname
    else:
        # Reject Annotations
        if not isinstance(txt_obj, LTAnno):
            for char_obj in txt_obj:
                return get_line_infos(char_obj)
        # If no LTChar object is found, return the BASE_FONT_SIZE and False
        return BASE_FONT_SIZE, False, None


def parse_pdf_document(pdffile):
    """ Given a path to a pdf, parse the file to return a PdfFile
    object, easier to analyse.
    """
    pdf_pages = []
    # Create all PDF resources needed by pdfminer.
    rsrcmgr = PDFResourceManager()
    laparams = LAParams(detect_vertical=True)
    device = PDFTextPageAggregator(rsrcmgr, laparams=laparams)
    # device = PDFTextPageAggregator(rsrcmgr)
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    pages = PDFPage.get_pages(
        pdffile,
        set(),
        caching=True,
        check_extractable=True
    )
    for page_num, page in enumerate(pages):
        pdf_lines = []
        has_bold = False

        # Process the page layout with pdfminer
        interpreter.process_page(page)
        layout = device.get_result()

        # Retrieve layouts objects
        for lt_obj in layout._objs:
            if type(lt_obj) in TEXT_ELEMENTS:
                # If the layout object contains text, iterate through its lines
                for txt_obj in lt_obj._objs:
                    # Retrieve informations (size, font face and bold)
                    font_size, bold, font_face = get_line_infos(txt_obj)

                    # We want bold lines to weight more to identofy titles
                    if bold:
                        has_bold = True
                        font_size += 1
                    else:
                        font_size -= 1

                    # Create a new PdfLine object and add it to the lines list
                    pdf_line = PdfLine(
                        int(math.ceil(font_size)),
                        bold,
                        txt_obj.get_text().strip(),
                        page_num,
                        font_face
                    )
                    pdf_lines.append(pdf_line)

        # Add a new PdfPage object containing the lines to the pages list
        pdf_pages.append(PdfPage(pdf_lines, page_num))

    # Create a new PdfFile with the pages
    pdf_file = PdfFile(pdf_pages, has_bold)
    return pdf_file


def parse_pdf_document_pdftxt(document):
    """ Given a path to a pdf, parse the file using pdftotext, to return a
    PdfFile object, easier to analyse.
    """

    logger = logging.getLogger(__name__)
    parsed_path = document.name.replace('.pdf', '.xml')
    cmd = [
            'pdftohtml',
            '-i',
            '-xml',
            document.name,
            parsed_path
            ]

    try:
        with open(os.devnull, 'w') as FNULL:
            subprocess.check_call(cmd, stdout=FNULL)
    except subprocess.CalledProcessError as e:
        logger.warning(
            "The pdf [%s] could not be converted: %s",
            document.name,
            e.sdterr,
        )
        return None

    html_file = open(parsed_path, 'rb')
    soup = bs(html_file.read(), 'html.parser')
    file_pages = []
    pages = soup.find_all('page')

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
    html_file.close()
    os.remove(parsed_path)
    return pdf_file


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
