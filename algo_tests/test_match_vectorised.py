import pandas as pd

from collections import Counter

from utils import FuzzyMatcher

def test_metric(test_info):
    """
    False positive rate or similar
    """

    metric = 50 # Place holder

    return metric

def test_match_vectorised(match_publications, test_publications, match_threshold):

    # Get the data into the same format as would be
    test_publications = test_publications.rename(columns={'Match title': 'Title', 'Match pub id': 'Reference id'})
    test_publications['Journal'] = None
    test_publications['PubYear'] = None
    test_publications['Authors'] = None
    test_publications['Issue'] = None
    test_publications['Volume'] = None
    test_publications['Document id'] = range(0, len(test_publications))
    test_publications['Document uri'] = None

    fuzzy_matcher = FuzzyMatcher(match_publications, match_threshold)

    match_data = fuzzy_matcher.match_vectorised(test_publications)

    test_info = pd.merge(
        test_publications[['Reference id', 'Type', 'Title', 'Document id']],
        match_data[['Reference id', 'uber_id', 'Cosine_Similarity', 'title']],
        on='Reference id', how='left'
        )

    test_score = test_metric(test_info)

    return test_info, test_score