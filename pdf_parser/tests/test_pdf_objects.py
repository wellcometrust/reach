from pdf_parser.pdf_parse import get_pdf_document, parse_pdf_document
from ..objects import PdfObjects
import unittest


TEST_PDF = 'pdf_parser/tests/pdfs/test_pdf.pdf'

"""Test file content (html transcription):
<h1>Test</h1>
Test
<b>Test bold</b>
<h1>References</h1>
<ol>
    <li>Test</li>
    <li>Test</li>
    <li>Test</li>
</ol>"""


class TestPdfObjects(unittest.TestCase):

    def setUp(self):
        self.test_file = open(TEST_PDF, 'rb')
        document = get_pdf_document(self.test_file)
        self.pdf_file_object = parse_pdf_document(document)

    def tearDown(self):
        self.test_file.close()

    def test_mean(self):
        font_mean = self.pdf_file_object.get_mean_font_size()
        self.assertEqual(font_mean, 17)

    def test_upper_mean(self):
        upper_mean = self.pdf_file_object.get_upper_mean_font_size()
        self.assertEqual(upper_mean, 18)

    def test_list_by_size(self):
        list_fonts = self.pdf_file_object.get_font_size_list()
        self.assertEqual(list_fonts, [18, 19, 15])

    def test_bold(self):
        list_bold_lines = self.pdf_file_object.get_bold_lines()
        for line in list_bold_lines:
            self.assertEqual(line.text, 'Test\tbold')

    def test_lines_by_keyword(self):
        keyword = 'bold'
        keyword_lines = self.pdf_file_object.get_lines_by_keyword(keyword)
        self.assertEqual(len(keyword_lines), 1)
        self.assertEqual('bold' in keyword_lines[0].text, True)
