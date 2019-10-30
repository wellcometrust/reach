import os.path


def get_path(p):
    return os.path.join(
        os.path.dirname(__file__),
        p
    )

TEST_PDF = get_path('pdfs/test_pdf.pdf')
TEST_PDF_MULTIPAGE = get_path('pdfs/test_pdf_multipage.pdf')
TEST_PDF_PAGE_NUMBER = get_path('pdfs/test_pdf_page_number.pdf')
TEST_XML = get_path('xml/test_xml.xml')
