import pandas as pd

from collections import Counter

from utils import FuzzyMatcher

def evaluate_metric(actual, predicted):
    """
    False positive rate or similar
    """
    test_scores = {'Score' : 50, 'More info' : "More information about this test"}

    return test_scores

def evaluate_match_references(match_publications, test_publications, match_threshold):

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

    # Does each publication have the correct match (1) or not (0)
    # There can be multiple matches found for each reference (WHICH EVENTUALLY SHOULD CHANGE)
    # Correct match if at least one of the matches is correct
    match_correct = []
    for i, test_publication in test_publications.iterrows():
        uberids = match_data.loc[match_data['Reference id'] == test_publication['Reference id']]['uber_id'].tolist()
        if (not uberids) or (test_publication['Reference id'] not in uberids):
            #  If there were no matches found for this reference or the id of the match was different
            match_correct.append(0)
        else:
            match_correct.append(1)
    test_publications['Matched correctly?'] = match_correct

    test_scores = evaluate_metric(test_publications['Type'], test_publications['Matched correctly?'])

    return test_scores