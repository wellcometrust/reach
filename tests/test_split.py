import unittest

from utils import _split_section, split_section
from refparse import SectionedDocument


class TestSplit(unittest.TestCase):

    def test_empty_sections(self):
        references = _split_section("")
        self.assertEqual(references, [], "Should be []")

    def test_oneline_section(self):
        references = _split_section("This is one line")
        self.assertEqual(
            references,
            ["This is one line"],
            "Should be ['This is one line']"
        )

    def test_empty_lines_section(self):
        references = _split_section("\n\n\n")
        self.assertEqual(references, [], "Should be []")

    def test_normal_section(self):
        references = _split_section(
            "One reference\nTwo references\nThree references\n"
        )
        self.assertEqual(
            references,
            ["One reference", "Two references", "Three references"],
            "Should be ['One reference', 'Two reference', 'Three reference']"
        )


class TestProcessReferenceSection(unittest.TestCase):

    def test_no_section_in_document(self):
        with self.assertRaises(AssertionError):
            split_section(None, '\n')
