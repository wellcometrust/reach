
from functools import partial
from collections import Counter

import pandas as pd
from sklearn.metrics import classification_report, f1_score, recall_score, precision_score

from policytool.refparse.utils import FuzzyMatcher

def predict_match_data(matcher, match_data):

    predictions = []
    for i, ref in match_data.iterrows():
        matched_publications = matcher.match_vectorised(ref)
        predictions.append(matched_publications['uber_id'][0])

    return predictions

def evaluate_metric(actual, predicted):

    predicted_bin = [a==p for (a,p) in zip(actual, predicted)]
    actual_bin = [True if a else False for a in actual]

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

    df_pairs = pd.DataFrame(
        [actual_types, predicted_types],
        index=["What did we expect?", "What did we find?"]
        ).T
    metrics = {
        'Score' : f1,
        'Micro average F1-score' : f1,
        'Micro average recall' : recall,
        'Micro average precision' : precision,
        'Classification report' : classification_report(
            actual_bin,
            predicted_bin
            ),
        'Frequency table of match types' : pd.crosstab(
            df_pairs["What did we find?"],
            df_pairs["What did we expect?"]
            )
        }

    return metrics

def evaluate_match_references(
        evaluation_references, match_threshold, sample_N
    ):

    # Take a random sample of the evaluation references to find matches for
    match_data = evaluation_references.sample(n = sample_N*2, random_state = 0).reset_index() 
    match_data['Title'] = match_data['title']

    match_data_positive = match_data.iloc[0:sample_N]
    match_data_negative = match_data.iloc[sample_N:]

    evaluation_references_without_negative = evaluation_references.loc[
        ~evaluation_references['uber_id'].isin(match_data_negative['uber_id'])
        ]

    fuzzy_matcher = FuzzyMatcher(evaluation_references_without_negative, match_threshold)

    predictions = predict_match_data(
        match_data=pd.concat([match_data_positive, match_data_negative]),
        matcher=fuzzy_matcher
        )
    actual = match_data_positive['Reference id'].to_list()+[None]*sample_N

    metrics = evaluate_metric(actual, predictions)

    return metrics
