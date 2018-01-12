import math
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfpage import PDFTextExtractionNotAllowed
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice
from pdfminer.layout import LAParams, LTTextBox, LTTextLine, LTChar, LTAnno
from pdfminer.converter import PDFPageAggregator
from .objects.PdfObjects import PdfFile, PdfPage, PdfLine
from .tools.extraction import _find_elements


BASE_FONT_SIZE = -10


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


def get_pdf_document(pdffile):
    """Create a pdf document for pdfminer lib."""
    parser = PDFParser(pdffile)
    # Provide password even if it's empty
    password = ''
    document = PDFDocument(parser, password)
    # Check if the document allows text extraction. If not, abort.
    if not document.is_extractable:
        raise PDFTextExtractionNotAllowed

    return document


def parse_pdf_document(document):
    """Given a pdfminer document object, parse the file to return a PdfFile
    object, easier to analyse.
    """
    pdf_pages = []

    # Create all PDF resources needed by pdfminer.
    rsrcmgr = PDFResourceManager()
    laparams = LAParams(detect_vertical=True)
    device = PDFPageAggregator(rsrcmgr, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)

    for page_num, page in enumerate(PDFPage.create_pages(document)):
        pdf_lines = []
        has_bold = False

        # Process the page layout with pdfminer
        interpreter.process_page(page)
        layout = device.get_result()

        # Retrieve layouts objects
        for lt_obj in layout._objs:
            if isinstance(lt_obj, LTTextBox) or isinstance(lt_obj, LTTextLine):
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
