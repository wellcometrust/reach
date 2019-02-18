import unittest

from pandas.util.testing import assert_frame_equal
import pandas as pd

from utils import FuzzyMatcher
from settings import settings


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
			fuzzy_matcher.real_publications, real_publications
		)
		self.assertEqual(
			fuzzy_matcher.threshold, threshold
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
		threshold = settings.FUZZYMATCH_THRESHOLD
		fuzzy_matcher = FuzzyMatcher(real_publications, threshold)
		return fuzzy_matcher

	def test_empty_predicted_publications(self):
		fuzzy_matcher = self.init_fuzzy_matcher()
		predicted_publications = pd.DataFrame({
			'Document id': [],
            'Reference id': [],
            'Title': []			
		})
		self.assertTrue(
			fuzzy_matcher.fuzzy_match(predicted_publications).size == 0
		) 

	def test_no_match(self):
		fuzzy_matcher = self.init_fuzzy_matcher()
		predicted_publications = pd.DataFrame({
			'Document id': [1],
            'Reference id': [1],
            'Title': ['Ebola']			
		})
		self.assertTrue(
			fuzzy_matcher.fuzzy_match(predicted_publications).size == 0
		) 

	def test_one_match(self):
		fuzzy_matcher = self.init_fuzzy_matcher()
		predicted_publications = pd.DataFrame({
			'Document id': [10],
            'Reference id': [11],
            'Title': ['Malaria']			
		})
		match_data = fuzzy_matcher.fuzzy_match(predicted_publications)
		self.assertEqual(match_data.shape[0], 1)
		self.assertEqual(match_data.iloc[0]['Document id'], 10)

	def test_close_match(self):
		real_publications = pd.DataFrame({
			'title': ['Malaria is caused by mosquitoes'],
			'uber_id': [1]
		})
		threshold = settings.FUZZYMATCH_THRESHOLD
		fuzzy_matcher = FuzzyMatcher(real_publications, threshold)
		predicted_publications = pd.DataFrame({
			'Document id': [10],
            'Reference id': [11],
            'Title': ['Malaria']			
		})
		match_data = fuzzy_matcher.fuzzy_match(predicted_publications)
		self.assertEqual(match_data.shape[0], 0) 
