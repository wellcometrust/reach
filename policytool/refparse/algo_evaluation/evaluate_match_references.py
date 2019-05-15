import pandas as pd

from sklearn.metrics import classification_report, f1_score

from utils import FuzzyMatcher

def evaluate_metric(actual, predicted):

    similarity = round(f1_score(actual, predicted, average='micro'), 3)

    test_scores = {
        'Score' : similarity,
        'Micro average F1-score' : similarity,
        'Classification report' : classification_report(actual, predicted) 
        }

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

    # Take out the negative reference id's (so you shouldn't find them)
    neg_test_pub_ids = test_publications.loc[test_publications['Type']==0]['Reference id']
    match_publications_no_negs = match_publications.loc[~match_publications['uber_id'].isin(neg_test_pub_ids)]

    fuzzy_matcher = FuzzyMatcher(match_publications_no_negs, match_threshold)

    match_data = fuzzy_matcher.match_vectorised(test_publications)

    # Does each publication have the correct match (True) or not (False)
    # (There might not be matches found for all the test_publications)
    merged_test_pred = pd.merge(test_publications, match_data, how="left", left_on='Reference id', right_on='Reference id')
    match_correct = merged_test_pred['Reference id']==merged_test_pred['uber_id']

    merged_test_pred['Matched correctly?'] = match_correct

    test_scores = evaluate_metric(merged_test_pred['Type'].astype(int), merged_test_pred['Matched correctly?'].astype(int))

    return test_scores