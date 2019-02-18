import unittest
import json
from pdf_parser.pdf_parse import parse_pdf_document
from pdf_parser.objects.PdfObjects import PdfFile

TEST_PDF = 'tests/pdfs/test_pdf.pdf'

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

JSON_PDF = json.dumps({
    'pages': [
        {
            'lines': [
                {
                    'size': 17,
                    'bold': True,
                    'text': 'Page 1 - Title 1',
                    'page_number': 1,
                    'font_face': 'Times',
                }
            ],
            'number': 1
        },
        {
            'lines': [
                {
                    'size': 17,
                    'bold': True,
                    'text': 'Page 2 - Title 2',
                    'page_number': 2,
                    'font_face': 'Times',
                },
                {
                    'size': 12,
                    'bold': False,
                    'text': 'Page 2 - Text 1',
                    'page_number': 2,
                    'font_face': 'Times',
                },
            ],
            'number': 2
        },
    ],
    'has_bold': True
})


class TestPdfObjects(unittest.TestCase):

    def setUp(self):
        self.test_file = open(TEST_PDF, 'rb')
        self.pdf_file_object = parse_pdf_document(self.test_file)

    def tearDown(self):
        self.test_file.close()

    def test_mean(self):
        font_mean = self.pdf_file_object.get_mean_font_size()
        self.assertTrue(font_mean in range(22, 25))

    def test_upper_mean(self):
        upper_mean = self.pdf_file_object.get_upper_mean_font_size()
        self.assertEqual(upper_mean, 29)

    def test_list_by_size(self):
        list_fonts = self.pdf_file_object.get_font_size_list()
        for i in list_fonts:
            self.assertTrue(i in [17, 29, 22])

    def test_bold(self):
        list_bold_lines = self.pdf_file_object.get_bold_lines()
        for line in list_bold_lines:
            self.assertEqual(line.text, 'Test bold')

    def test_page_text(self):
        page_text = self.pdf_file_object.get_page(0).get_page_text(
            ignore_page_numbers=True
        )
        self.assertTrue(len(page_text) > 0)

    def test_lines_by_keyword(self):
        keyword = 'References'
        keyword_lines = self.pdf_file_object.get_lines_by_keyword(keyword)
        self.assertEqual(len(keyword_lines), 1)
        self.assertEqual('References' in keyword_lines[0], True)

    def test_lines_by_keywords(self):
        keywords = ['bold', 'test', 'machine']
        keyword_lines = self.pdf_file_object.get_lines_by_keywords(keywords)
        self.assertTrue('bold' in keyword_lines.keys())
        self.assertEqual(len(keyword_lines['bold']), 1)
        self.assertTrue('test' in keyword_lines.keys())
        self.assertTrue(len(keyword_lines['test']) in [5, 6])
        self.assertEqual('bold' in keyword_lines['bold'][0], True)

    def test_lines_by_keywords_and_context(self):
        keywords = ['bold', 'test', 'machine']
        keyword_lines = self.pdf_file_object.get_lines_by_keywords(keywords, 2)
        self.assertTrue('bold' in keyword_lines.keys())
        self.assertEqual(len(keyword_lines['bold']), 5)
        self.assertTrue('test' in keyword_lines.keys())
        self.assertTrue(len(keyword_lines['test']) in [22, 24])

    def test_from_json(self):
        pdf_file = PdfFile()
        pdf_file.from_json(JSON_PDF)
        self.assertTrue(len(pdf_file.pages) == 2)

    def test_to_json(self):
        pdf_file = PdfFile()
        pdf_file.from_json(JSON_PDF)
        pdf_export = pdf_file.to_json()
        self.assertEqual(pdf_export, JSON_PDF)
