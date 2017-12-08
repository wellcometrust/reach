from tools.extraction import _find_elements, grab_section
from pdf_parse import get_pdf_document, parse_pdf_document
import unittest

TEST_PDF = 'tests/pdfs/test_pdf.pdf'


class TestTools(unittest.TestCase):

    def setUp(self):
        self.test_file = open(TEST_PDF, 'rb')
        document = get_pdf_document(self.test_file)
        self.pdf_file_object = parse_pdf_document(document)

    def tearDown(self):
        self.test_file.close()

    def test_element_finder(self):
        elements = _find_elements(self.pdf_file_object, 'Reference')
        self.assertEqual(elements, [])
