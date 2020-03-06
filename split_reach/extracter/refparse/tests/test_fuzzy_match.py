import pandas as pd
import pytest
from pandas.util.testing import assert_frame_equal
from reach.refparse.utils import FuzzyMatcher


@pytest.fixture
def fuzzy_matcher():
    real_publications = [
        {'title': 'Malaria', 'pmcid': 0},
        {'title': 'Zika', 'pmcid': 1},
    ]
    fuzzy_matcher = FuzzyMatcher(real_publications, similarity_threshold=0.75)

    return fuzzy_matcher

def test_empty_list():
    real_publications = []
    with pytest.raises(ValueError):
        FuzzyMatcher(real_publications, similarity_threshold=0.75)

def test_no_titles():
    real_publications = [{}, {}, {}]
    with pytest.raises(ValueError):
        FuzzyMatcher(real_publications, similarity_threshold=0.75)

def test_no_string_titles():
    real_publications = [{'title':1}, {'title':2}]
    with pytest.raises(AttributeError):
        FuzzyMatcher(real_publications, similarity_threshold=0.75)

def test_init_variables():
    real_publications = [
        {'title': 'Malaria', 'pmcid': 0},
        {'title': 'Zika', 'pmcid': 1},
    ]

    threshold = 0.75
    fuzzy_matcher = FuzzyMatcher(real_publications, threshold)
    assert isinstance(fuzzy_matcher.publications, dict)
    assert isinstance(fuzzy_matcher.publications[0], dict)
    assert fuzzy_matcher.publications[0] == real_publications[0]
    assert fuzzy_matcher.similarity_threshold == threshold
    assert fuzzy_matcher.tfidf_matrix.size != 0



def test_empty_reference(fuzzy_matcher):
    reference = {}
    assert fuzzy_matcher.match(reference) is None

def test_no_match(fuzzy_matcher):
    reference = {
        'Document id': 1,
        'Reference id': 1,
        'Title': 'Ebola'
    }
    assert fuzzy_matcher.match(reference) is None

def test_one_match(fuzzy_matcher):
    reference = {
        'Document id': '10',
        'Reference id': '11',
        'Title': 'Malaria'
    }
    matched_publication = fuzzy_matcher.match(reference)
    assert matched_publication['Document id'] == '10'

def test_close_match():
    real_publications = [
        {'title': 'Malaria is caused by mosquitos', 'pmcid': 0},
    ]
    fuzzy_matcher = FuzzyMatcher(real_publications, similarity_threshold=0.75)

    reference = {
        'Document id':  '10',
        'Reference id': '11',
        'Title': 'Malaria',
    }

    matched_publication = fuzzy_matcher.match(reference)
    assert matched_publication is None

@pytest.mark.xfail(strict=True)
def test_close_match_reverse(fuzzy_matcher):
    """
    This test is included to highlight somewhat unexpected behaviour, where
    matches do not work in both directions. Compare to test above.
    """

    reference = {
        'Document id':  '10',
        'Reference id': '11',
        'Title': 'Malaria is caused by mosquitos',
    }

    matched_publication = fuzzy_matcher.match(reference)
    assert matched_publication is None
