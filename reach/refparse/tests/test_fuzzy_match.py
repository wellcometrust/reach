import unittest

from pandas.util.testing import assert_frame_equal
import pandas as pd

from reach.refparse.utils import FuzzyMatcher
from reach.refparse.settings import settings


class TestFuzzyMatcherInit(unittest.TestCase):
    def test_empty_title(self):
        real_publications = pd.DataFrame({
            'title': []
        })
        threshold = 75
        with self.assertRaises(ValueError):
            FuzzyMatcher(real_publications, threshold)

    def test_no_title(self):
        real_publications = pd.DataFrame({})
        threshold = 75
        with self.assertRaises(KeyError):
            FuzzyMatcher(real_publications, threshold)

    def test_no_string_titles(self):
        real_publications = pd.DataFrame({
            'title': [1,2]
        })
        threshold = 75
        with self.assertRaises(AttributeError):
            FuzzyMatcher(real_publications, threshold)

    def test_init_variables(self):
        real_publications = pd.DataFrame({
            'title': ['Malaria', 'Zika']
        })
        threshold = 0
        fuzzy_matcher = FuzzyMatcher(real_publications, threshold)
        assert_frame_equal(
            fuzzy_matcher.publications, real_publications
        )
        self.assertEqual(
            fuzzy_matcher.similarity_threshold, threshold
        )
        self.assertTrue(
            fuzzy_matcher.tfidf_matrix.size != 0
        )

class TestFuzzyMatch(unittest.TestCase):
    def init_fuzzy_matcher(self):
        real_publications = pd.DataFrame({
            'title': ['Malaria', 'Zika'],
            'uber_id': [1, 2]
        })
        threshold = settings.FUZZYMATCH_SIMILARITY_THRESHOLD
        fuzzy_matcher = FuzzyMatcher(real_publications, threshold)
        return fuzzy_matcher

    def test_empty_reference(self):
        fuzzy_matcher = self.init_fuzzy_matcher()
        reference = {}
        self.assertTrue(
            fuzzy_matcher.match(reference) is None
        ) 

    def test_no_match(self):
        fuzzy_matcher = self.init_fuzzy_matcher()
        reference = {
            'Document id': 1,
            'Reference id': 1,
            'Title': 'Ebola'            
        }
        self.assertTrue(
            fuzzy_matcher.match(reference) is None 
        ) 

    def test_one_match(self):
        fuzzy_matcher = self.init_fuzzy_matcher()
        reference = {
            'Document id': 10,
            'Reference id': 11,
            'Title': 'Malaria'            
        }
        matched_publication = fuzzy_matcher.match(reference)
        self.assertEqual(matched_publication['Document id'], 10)

    def test_close_match(self):
        real_publications = pd.DataFrame({
            'title': ['Malaria is caused by mosquitoes'],
            'uber_id': [1]
        })
        threshold = settings.FUZZYMATCH_SIMILARITY_THRESHOLD
        fuzzy_matcher = FuzzyMatcher(real_publications, threshold)
        reference = {
            'Document id': 10,
            'Reference id': 11,
            'Title': 'Malaria'            
        }
        matched_publication = fuzzy_matcher.match(reference)
        self.assertEqual(matched_publication, None) 
