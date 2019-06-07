import unittest

import dill
import os

from policytool.refparse.utils import split_section
from policytool.refparse.refparse import SectionedDocument

MODELS_DIR = os.path.join(os.path.dirname(__file__), '..', 'reference_splitter_models')

with open(os.path.join(MODELS_DIR, "line_iobe_pipeline_20190502.dll"), "rb") as f:
    model = dill.load(f)

class TestSplit(unittest.TestCase):

    def test_empty_sections(self):
        references = split_section("", model)
        self.assertEqual(references, [], "Should be []")

    def test_oneline_section(self):
        references = split_section("This is one line", model)
        self.assertEqual(
            references,
            ["This is one line"],
            "Should be ['This is one line']"
        )

    def test_empty_lines_section(self):
        references = split_section("\n\n\n", model)
        self.assertEqual(references, [], "Should be []")

    def test_normal_section(self):
        references = split_section(
            "One reference\nTwo references\nThree references\n",
            model
        )
        self.assertEqual(
            references,
            ["One reference", "Two references", "Three references"],
            "Should be ['One reference', 'Two reference', 'Three reference']"
        )
