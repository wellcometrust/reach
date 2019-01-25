import unittest

from utils import predict_references

import pickle

pickle_in = open("./reference_parser_models/RefSorter_classifier.pkl","rb")
mnb = pickle.load(pickle_in)

pickle_in = open("./reference_parser_models/RefSorter_vectorizer.pkl","rb")
vectorizer = pickle.load(pickle_in)

class TestSplit(unittest.TestCase):
	def test_empty_components(self):
		components_predictions = predict_references(mnb,vectorizer,"")
		self.assertEqual(components_predictions, [], "Should be []")

	def test_normal_components(self):
		components_predictions = predict_references(mnb,vectorizer,["Component","Component","Component"])
		self.assertEqual(isinstance(components_predictions, list) , True, "Should be a list")

	def test_size(self):
		components_predictions = predict_references(mnb,vectorizer,["Component","Component","Component"])
		self.assertEqual(len(components_predictions) , 3, "Should be 3")

	def test_author_component(self):
		components_predictions = predict_references(mnb,vectorizer,["Component"])
		self.assertEqual(isinstance(components_predictions[0][0], str), True, "Should be a string")

	def test_year_component(self):
		components_predictions = predict_references(mnb,vectorizer,["1999"])
		self.assertEqual(components_predictions[0][0], 'PubYear', "Should be 'PubYear'")
