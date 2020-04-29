import os.path
import unittest
import pickle

import pytest

from refparse.utils import structure_reference
from refparse.refparse import SectionedDocument
from deep_reference_parser.split_parse import SplitParser

splitter_parser = SplitParser(config_file=os.path.join(
    os.path.dirname(__file__), 'test_config_multitask.ini')
)

class TestSplitParse(unittest.TestCase):

    def test_empty_sections(self):
        references = splitter_parser.split_parse(" ")
        assert references == [], "Should be []"

    @pytest.mark.xfail()
    def test_oneline_section(self):
        references = splitter_parser.split_parse("References. Smith et al. 2019. This is a title. Journal of journals. 1-2")
        assert len(references) == 1, "There should be 1 reference found"

    def test_oneline_section_brackets(self):
        references = splitter_parser.split_parse("References. Smith et al. (2019). This is a title. Journal of journals. 1-2")
        assert len(references) == 1, "There should be 1 reference found"

    def test_empty_lines_section(self):
        references = splitter_parser.split_parse("\n\n\n")
        assert references == [], "Should be []"

    @pytest.mark.xfail()
    def test_normal_section(self):
        references = splitter_parser.split_parse(
            "References \n1. Smith et al. 2019. This is a title. Journal of journals. 1-2. "+
            "\n2. Smith et al. 2019. This is a title. Journal of journals. 1-2. "+
            "\n3. Smith et al. 2019. This is a title. Journal of journals. 1-2."
        )

        assert len(references) == 3, "There should be 3 reference found"

    def test_normal_section_brackets(self):
        references = splitter_parser.split_parse(
            "References \n1. Smith et al. (2019). This is a title. Journal of journals. 1-2. "+
            "\n2. Smith et al. (2019). This is a title. Journal of journals. 1-2. "+
            "\n3. Smith et al. (2019). This is a title. Journal of journals. 1-2."
        )

        assert len(references) == 3, "There should be 3 reference found"

class TestStructure(unittest.TestCase):
    def test_empty_components(self):
        components_predictions = structure_reference([])
        self.assertEqual(components_predictions.get('Title'), '', "Should be ''")

    def test_size(self):
        components_predictions = structure_reference([])
        self.assertEqual(len(components_predictions), 7, "Should be 7 classes predicted")

    def test_string_component(self):
        reference_components = [
            ('Medecins', 'author'), ('Sans', 'author'), ('Frontières', 'author'),
            ('.', 'o'), ('TB', 'title'), ('Spot', 'title'), ('Report', 'title'),
            ('.', 'o'), ('2011', 'year')]
        components_predictions = structure_reference(reference_components)
        self.assertEqual(isinstance(components_predictions['Title'], str), True, "Should be a string")

    def test_normal_components(self):
        reference_components = [
            ('Medecins', 'author'), ('Sans', 'author'), ('Frontières', 'author'),
            ('.', 'o'), ('TB', 'title'), ('Spot', 'title'), ('Report', 'title'),
            ('.', 'o'), ('2011', 'year')]
        components_predictions = structure_reference(reference_components)
        self.assertEqual(components_predictions['Title'], 'TB Spot Report', "Should be 'TB Spot Report'")

    def test_split_title(self):
        reference_components = [
            ('TB', 'title'), ('Spot', 'author'), ('Report', 'title')]
        components_predictions = structure_reference(reference_components)
        self.assertEqual(components_predictions['Title'], 'TB Report', "Should be 'TB Report'")

