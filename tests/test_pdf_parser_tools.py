import unittest
from pdf_parser.tools.extraction import _find_elements
from pdf_parser.pdf_parse import parse_pdf_document

TEST_PDF = 'tests/pdfs/test_pdf.pdf'


class TestTools(unittest.TestCase):

    def setUp(self):
        self.test_file = open(TEST_PDF, 'rb')
        self.pdf_file_object, self.text = parse_pdf_document(self.test_file)

    def tearDown(self):
        self.test_file.close()

    def test_element_finder(self):
        elements = _find_elements(self.pdf_file_object, 'Reference')
        self.assertEqual(elements, [])
