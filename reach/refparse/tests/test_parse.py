import os.path
import unittest
import pickle

from reach.refparse.utils import \
    predict_components, merge_components, split_reference

MODELS_DIR = os.path.join(os.path.dirname(__file__), '..', 'reference_parser_models')

with open(os.path.join(MODELS_DIR, "reference_parser_pipeline.pkl"), "rb") as f:
    model = pickle.load(f)


class TestPredict(unittest.TestCase):
    def test_empty_components(self):
        components_predictions = predict_components(model,[])
        self.assertEqual(components_predictions, [], "Should be []")

    def test_normal_components(self):
        components_predictions = predict_components(model,["Component","Component","Component"])
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
        components_predictions = predict_components(model,["Component","Component","Component"])
        self.assertEqual(len(components_predictions) , 3, "Should be 3")

    def test_string_component(self):
        components_predictions = predict_components(model,["Component"])
        self.assertEqual(isinstance(components_predictions[0]['Predicted Category'], str), True, "Should be a string")

    def test_year_component(self):
        components_predictions = predict_components(model,["1999"])
        self.assertEqual(components_predictions[0]['Predicted Category'], 'PubYear', "Should be 'PubYear'")


class TestSplit(unittest.TestCase):
    def test_no_reference(self):
        self.assertEqual(split_reference(None), [], "Should be []")

    def test_empty_reference(self):
        self.assertEqual(split_reference(""), [], "Should be []")

    def test_no_element_to_split(self):
        self.assertEqual(
            split_reference("This is a reference"),
            ["This is a reference"],
            "Should be a list with one element"
        )

    def test_split_by_comma(self):
        self.assertEqual(
            split_reference("This, is a reference"),
            ["This", "is a reference"],
            "Should be a list with two elements"
        )

    def test_split_by_question_mark(self):
        self.assertEqual(
            split_reference("To be? Or not to be?"),
            ["To be", "Or not to be"],
            "Should be a list with two elements"
        )

    def test_split_by_exclamation_mark(self):
        self.assertEqual(
            split_reference("To be! What a silly question"),
            ["To be", "What a silly question"],
            "Should be a list with two elements"
        )


class TestMerge(unittest.TestCase):
    def test_empty_components(self):
        self.assertEqual(merge_components([]), [], "Should be []")

    def test_incorrect_classes_passed(self):
        components = [
            {'Predicted Category': 'Junk'},
            {'Predicted Category': 'Apple'},
            {'Predicted Category': 'Google'}
        ]
        empty_structured_components = {
            'Authors': '',
            'Volume': '',
            'Journal': '',
            'Title': '',
            'Pagination': '',
            'Issue': '',
            'PubYear': ''
        }
        self.assertEqual(
            merge_components(components),
            empty_structured_components,
            "Should be {}".format(empty_structured_components)
        )

    def test_all_classes_returned(self):
        components = [
            {
                'Predicted Category': 'Title',
                'Prediction Probability': 1,
                'Reference component': 'This is a title.'
            },
        ]
        expected_structured_components = {
            'Authors': '',
            'Volume': '',
            'Journal': '',
            'Title': 'This is a title.',
            'Pagination': '',
            'Issue': '',
            'PubYear': ''
        }
        self.assertEqual(
            merge_components(components),
            expected_structured_components,
            "Should be {}".format(expected_structured_components)
        )

    def test_merge_works(self):
        components = [
            {
                'Predicted Category': 'Title',
                'Prediction Probability': 1,
                'Reference component': 'This'
            },
            {
                'Predicted Category': 'Title',
                'Prediction Probability': 1,
                'Reference component': 'is a title.'
            },
            {
                'Predicted Category': 'Authors',
                'Prediction Probability': 1,
                'Reference component': 'Nick'
            },
        ]
        expected_structured_components = {
            'Authors': 'Nick',
            'Volume': '',
            'Journal': '',
            'Title': 'This, is a title.',
            'Pagination': '',
            'Issue': '',
            'PubYear': ''
        }
        self.assertEqual(
            merge_components(components),
            expected_structured_components,
            "Should be {}".format(expected_structured_components)
        )
