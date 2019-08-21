import unittest

from policytool.refparse.utils import split_section
from policytool.refparse.refparse import SectionedDocument


class TestSplit(unittest.TestCase):

    def test_empty_sections(self):
        references = split_section("")
        self.assertEqual(references, [], "Should be []")

    def test_oneline_section(self):
        references = split_section("This is one line")
        self.assertEqual(
            references,
            ["This is one line"],
            "Should be ['This is one line']"
        )

    def test_empty_lines_section(self):
        references = split_section("\n\n\n")
        self.assertEqual(references, [], "Should be []")

    def test_normal_section(self):
        references = split_section(
            "1. One reference\n2. Two references\n3. Three references\n"
        )
        self.assertEqual(
            references,
            ["1. One reference", "\n2. Two references", "\n3. Three references\n"],
            "Should be ['One reference', 'Two reference', 'Three reference']"
        )
