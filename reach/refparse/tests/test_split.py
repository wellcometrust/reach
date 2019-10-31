import unittest

from reach.refparse.utils import split_section
from reach.refparse.refparse import SectionedDocument


class TestSplit(unittest.TestCase):

    def test_empty_sections(self):
        references = split_section(" ")
        self.assertEqual(references, [], "Should be []")

    def test_oneline_section(self):
        references = split_section("Smith et al. 2019. This is a title. Journal of journals. 1-2")
        self.assertEqual(
            len(references),
            1,
            "There should be 1 reference found"
        )

    def test_empty_lines_section(self):
        references = split_section("\n\n\n")
        self.assertEqual(references, [], "Should be []")

    def test_normal_section(self):
        references = split_section(
            "References \n1. Smith et al. 2019. This is a title. Journal of journals. 1-2. "+
            "\n2. Smith et al. 2019. This is a title. Journal of journals. 1-2. "+
            "\n3. Smith et al. 2019. This is a title. Journal of journals. 1-2."
        )
        self.assertEqual(
            len(references),
            3,
            "There should be 3 references found"
        )
