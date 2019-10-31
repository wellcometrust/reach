import unittest
from collections import namedtuple

from pandas.util.testing import assert_frame_equal
import pandas as pd

from policytool.refparse.utils import ExactMatcher
from policytool.refparse.settings import settings

SectionedDocument = namedtuple(
    'SectionedDocument',
    ['section', 'id']
)

class TestExactMatcherInit(unittest.TestCase):

    def test_no_section(self):
        doc_texts = [()]
        threshold = 3
        with self.assertRaises(AttributeError):
            ExactMatcher(doc_texts, threshold)

    def test_no_string_section(self):
        doc_texts = [
            SectionedDocument(1, 123)
            ]

        threshold = 3
        with self.assertRaises(TypeError):
            ExactMatcher(doc_texts, threshold)

    def test_init_variables(self):
        doc_texts = [
            SectionedDocument("Malaria", 123)
            ]
        threshold = 3
        exact_matcher = ExactMatcher(doc_texts, threshold)
        self.assertEqual(exact_matcher.texts, [(123, "malaria")])
        self.assertEqual(
            exact_matcher.title_length_threshold, threshold
        )

class TestExactMatch(unittest.TestCase):
    def init_exact_matcher(self):
        doc_texts = [
            SectionedDocument("Malaria", 123)
            ]
        threshold = 3
        exact_matcher = ExactMatcher(doc_texts, threshold)
        return exact_matcher

    def test_empty_publication(self):
        exact_matcher = self.init_exact_matcher()
        publication = {}
        matched_text_generator = exact_matcher.match(publication)
        with self.assertRaises(KeyError):
            next(matched_text_generator)

    def test_no_match(self):
        exact_matcher = self.init_exact_matcher()
        publication = {
            'uber_id': 1,
            'title': "Ebola"
        }
        matched_text_generator = exact_matcher.match(publication)
        self.assertEqual(len(list(matched_text_generator)), 0)

    def test_one_match(self):
        exact_matcher = self.init_exact_matcher()
        publication = {
            'uber_id': 1,
            'title': "Malaria"
        }
        matched_text_generator = exact_matcher.match(publication)
        self.assertEqual(next(matched_text_generator)['Document id'], 123)

    def test_close_match(self):
        exact_matcher = self.init_exact_matcher()
        publication = {
            'uber_id': 1,
            'title': "MalariaX"
        }
        matched_text_generator = exact_matcher.match(publication)
        self.assertEqual(len(list(matched_text_generator)), 0)

    def test_threshold(self):
        doc_texts = [
            SectionedDocument("Malaria", 0)
            ]
        threshold = 8
        exact_matcher = ExactMatcher(doc_texts, threshold)

        publication = {
            'uber_id': 1,
            'title': "Malaria"
        }
        matched_text_generator = exact_matcher.match(publication)
        self.assertEqual(len(list(matched_text_generator)), 0)
