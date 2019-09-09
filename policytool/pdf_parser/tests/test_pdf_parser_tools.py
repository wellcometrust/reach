import unittest

from policytool.pdf_parser.tools.extraction import _find_elements
from policytool.pdf_parser.pdf_parse import parse_pdf_document
from policytool.scraper.tests.common import TEST_PDF


class TestTools(unittest.TestCase):

    def setUp(self):
        self.test_file = open(TEST_PDF, 'rb')
        self.pdf_file_object, _, errors = parse_pdf_document(self.test_file)
        assert not errors

    def tearDown(self):
        self.test_file.close()

    def test_element_finder(self):
        elements = _find_elements(self.pdf_file_object, 'Reference')
        self.assertEqual(elements, [])
