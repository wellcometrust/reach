import os.path
import unittest
import pickle

from utils import predict_references

MODELS_DIR = os.path.join(os.path.dirname(__file__), '..', 'reference_parser_models')

with open(os.path.join(MODELS_DIR, "RefSorter_classifier.pkl"), "rb") as f:
    mnb = pickle.load(f)

with open(os.path.join(MODELS_DIR, "RefSorter_vectorizer.pkl"), "rb") as f:
    vectorizer = pickle.load(f)

class TestPredict(unittest.TestCase):
	def test_empty_components(self):
		components_predictions = predict_references(map,mnb,vectorizer,[])
		self.assertEqual(components_predictions, [], "Should be []")

	def test_normal_components(self):
		components_predictions = predict_references(map,mnb,vectorizer,["Component","Component","Component"])
		all_categories = ['Authors', 'Title', 'Journal', 'PubYear', 'Volume', 'Issue', 'Pagination']
		self.assertEqual(
			isinstance(components_predictions, list),
			True, "Should be a list"
			)
		self.assertEqual(
			all([components_prediction['Predicted Category'] in all_categories for components_prediction in components_predictions]),
			True, "Should be a list of categories from {}".format(all_categories)
			)

	def test_size(self):
		components_predictions = predict_references(map,mnb,vectorizer,["Component","Component","Component"])
		self.assertEqual(len(components_predictions) , 3, "Should be 3")

	def test_string_component(self):
		components_predictions = predict_references(map,mnb,vectorizer,["Component"])
		self.assertEqual(isinstance(components_predictions[0]['Predicted Category'], str), True, "Should be a string")

	def test_year_component(self):
		components_predictions = predict_references(map,mnb,vectorizer,["1999"])
		self.assertEqual(components_predictions[0]['Predicted Category'], 'PubYear', "Should be 'PubYear'")


