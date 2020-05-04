import unittest
import pytest

from refparse.utils import structure_reference

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

