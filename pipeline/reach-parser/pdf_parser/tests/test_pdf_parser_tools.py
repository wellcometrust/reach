import unittest

from lxml import etree

from pdf_parser.pdf_parse import parse_pdf_document
from pdf_parser.tools.extraction import (_find_elements,
                                                    _flatten_text,
                                                    _flatten_fontspec)
from tests.common import TEST_PDF, TEST_XML


class TestTools(unittest.TestCase):

    def setUp(self):
        self.test_file = open(TEST_PDF, 'rb')
        self.pdf_file_object, _, _, errors = parse_pdf_document(self.test_file)
        assert not errors

    def tearDown(self):
        self.test_file.close()

    def test_element_finder(self):
        elements = _find_elements(self.pdf_file_object, 'Reference')
        self.assertEqual(elements, [])

class TestFlattenTools(unittest.TestCase):

    def setUp(self):

        self.test_file = open(TEST_XML, 'r')
        tree = etree.parse(self.test_file)
        self.fontspecs = tree.xpath('//fontspec')
        self.texts = tree.xpath('//text')

    def tearDown(self):
        #self.test_file.close()
        pass

    def test_flatten_text(self):
        text = _flatten_text(self.texts[0])
        self.assertEqual(text, "Test Page 1")
        self.assertIs(type(text), str)

    def test_flatten_texts(self):
        """ Ensure that _flatten_text adequately captures text with formatting.
        """
        texts = [_flatten_text(i) for i in self.texts]
        self.assertIs(type(texts), list)
        self.assertIs(len(texts), 10)
        self.assertEqual(texts[1], 'All bold line.')
        self.assertEqual(texts[2], 'Partly  bold  line.')
        self.assertEqual(texts[3], 'All italic line.')
        self.assertEqual(texts[4], 'Partly  italic  line.')

    def test_flatten_fontspec(self):
        font_map = _flatten_fontspec(self.fontspecs)
        self.assertEqual(len(font_map), 2)
        self.assertIs(type(font_map), dict)
