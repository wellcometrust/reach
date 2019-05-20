import pandas as pd

from sklearn.metrics import classification_report, f1_score

from utils import FuzzyMatcher

def evaluate_metric(actual, predicted):

    actual_binary = actual.astype(int)
    # predicted is True, False and "No match found",
    # convert to 1 (True) or 0 (False or "No match found")
    predicted_binary = [1 if pred_type==True else 0 for pred_type in predicted]

    similarity = round(f1_score(actual_binary, predicted_binary, average='micro'), 3)

    test_scores = {
        'Score' : similarity,
        'Micro average F1-score' : similarity,
        'Classification report' : classification_report(actual_binary, predicted_binary),
        'Frequency table of match types' : pd.crosstab(index=actual, columns=predicted) 
        }

    return test_scores

def evaluate_match_references(publications, evaluation_references, match_threshold):
    """
    Try to match the evaluation_references with references in 'publications'
    """

    # Get the data into the same format as would be
    evaluation_references = evaluation_references.rename(columns={'Match title': 'Title', 'Match pub id': 'Reference id'})
    evaluation_references['Document id'] = range(0, len(evaluation_references))

    # Take out the negative reference id's (so you shouldn't find them)
    neg_test_pub_ids = evaluation_references.loc[evaluation_references['Do we expect a match?']==0]['Reference id']
    publications_no_negs = publications.loc[~publications['uber_id'].isin(neg_test_pub_ids)]

    fuzzy_matcher = FuzzyMatcher(publications_no_negs, match_threshold)

    matched_publications = fuzzy_matcher.match_vectorised(evaluation_references)

    evaluation_matches = pd.merge(evaluation_references, matched_publications, how="left", left_on='Reference id', right_on='Reference id')

    # Does each publication have the correct match (true), an incorrect match (false) or no match
    evaluation_matches['Matched correctly?'] = [
        matches['Reference id']==matches['uber_id'] if not pd.isnull(matches['uber_id'])\
        else "No match found"\
        for _, matches in evaluation_matches.iterrows()
        ]

    test_scores = evaluate_metric(evaluation_matches['Do we expect a match?'], evaluation_matches['Matched correctly?'])

    return test_scores
