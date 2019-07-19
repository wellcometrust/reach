
from functools import partial
from collections import Counter

import pandas as pd
from sklearn.metrics import classification_report, f1_score, recall_score, precision_score

from policytool.refparse.utils import FuzzyMatcher

def predict_match_data(matcher, match_data):
    """
    Input: 
        matcher: A matcher object initialised
                on a corpus of references (e.g. all of EPMC)
        match_data: A pandas dataframe with the
                references you want to find title matches for
                in the corpus (e.g. references found in policy documents).
                This must have a column called 'Title'
                and two unique identifier columns 'Document id'
                and 'Reference id'.
    Output:
        predictions: A dataframe of the reference matches found using
                the matcher function. Each line will have 'Reference id'
                from the match_data references, and if it matched a 
                reference from the corpus references then the 'Matched publication id'
                of this reference will be given. If there was no match
                the Matched publication id column will be None. The 'Cosine Similarity'
                column gives the score of how similar the matched 
                reference titles are.
    """

    predictions = []
    for i, ref in match_data.iterrows():
        matched_publications = matcher.match(ref)
        if matched_publications:
            predictions.append(matched_publications['Matched publication id'])
        else:
            predictions.append(None)

    return predictions

def evaluate_metric(actual, predicted):
    """
    Input:
        actual: A list of the reference ids expected to be matched to
                when a list of references were passed through the
                matcher function. If no match is expected then this is None.
        predicted: A list of the reference ids found to be matched
                when a list of references were passed through the
                matcher function. This is set to None if none
                were found.

    Output:
        metrics: Various metrics for how similar these lists are.
    """

    # Convert the reference id lists to binary - for the match to be correct the
    # two ids need to be the same, which includes if they are both None.
    actual_bin = [True if a else False for a in actual]
    predicted_bin = [((a and a==p) or (not a and a!=p)) for (a,p) in zip(actual, predicted)]

    f1 = round(f1_score(actual_bin, predicted_bin, average='micro'), 3)
    recall = round(recall_score(actual_bin, predicted_bin, average='micro'), 3)
    precision = round(precision_score(actual_bin, predicted_bin, average='micro'), 3)

    actual_types = ["Match expected" if a else "No match expected" for a in actual]
    predicted_types = []
    for (a,p) in zip(actual, predicted):
        if p:
            if a==p:
                predicted_types.append("Correct match found")
            else:
                predicted_types.append("Incorrect match found")
        else:
            predicted_types.append("No match found")
    actual_predicted_pairs = pd.DataFrame(
        [actual_types, predicted_types],
        index=["What did we expect?", "What did we find?"]
        ).T

    metrics = {
        'Score' : f1,
        'Number of references in sample' : len(actual),
        'Micro average F1-score' : f1,
        'Micro average recall' : recall,
        'Micro average precision' : precision,
        'Classification report' : classification_report(
            actual_bin,
            predicted_bin
            ),
        'Frequency table of match types' : pd.crosstab(
            actual_predicted_pairs["What did we find?"],
            actual_predicted_pairs["What did we expect?"]
            )
        }

    return metrics

def evaluate_match_references(
        evaluation_references, match_threshold, length_threshold, sample_N
    ):

    # Take a random sample of the evaluation references to find matches for
    match_data = evaluation_references.sample(n = sample_N*2, random_state = 0).reset_index() 
    match_data['Title'] = match_data['title']

    match_data_positive = match_data.iloc[0:sample_N]
    match_data_negative = match_data.iloc[sample_N:]

    evaluation_references_without_negative = evaluation_references.loc[
        ~evaluation_references['uber_id'].isin(match_data_negative['uber_id'])
        ]

    fuzzy_matcher = FuzzyMatcher(evaluation_references_without_negative, match_threshold, length_threshold)

    predictions = predict_match_data(
        match_data=pd.concat([match_data_positive, match_data_negative]),
        matcher=fuzzy_matcher
        )
    actual = match_data_positive['Reference id'].to_list()+[None]*sample_N

    metrics = evaluate_metric(actual, predictions)

    return metrics
