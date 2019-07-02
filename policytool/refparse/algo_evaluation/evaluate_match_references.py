import pandas as pd
from functools import partial

from sklearn.metrics import classification_report, f1_score, recall_score, precision_score

from policytool.refparse.utils import FuzzyMatcher


def predict_match_data(matcher, match_data, match_threshold, length_threshold):

    matched_publications = matcher.match_vectorised(match_data)

    predictions = []
    for _, match in matched_publications.iterrows():
        if (
            match['Cosine_Similarity'] > match_threshold and 
            len(match['Title']) > length_threshold
        ):
            if match['uber_id'] == match['Reference id']:
                predictions.append("Positive - correct match")
            else:
                predictions.append("Positive - incorrect match")
        else:
            if match['uber_id'] == match['Reference id']:
                predictions.append("Negative - correct match")
            else:
                predictions.append("Negative - incorrect match")

    return predictions

def evaluate_metric(actual, predicted):

    actual_binary = ["Positive" if "Positive" in actual_type else "Negative" for actual_type in actual]
    predicted_binary = ["Positive" if "Positive" in pred_type else "Negative" for pred_type in predicted]

    f1 = round(f1_score(actual_binary, predicted_binary, average='micro'), 3)
    recall = round(recall_score(actual_binary, predicted_binary, average='micro'), 3)
    precision = round(precision_score(actual_binary, predicted_binary, average='micro'), 3)

    df_pairs = pd.DataFrame(
        [actual, predicted],
        index=["Do we expect to find the correct match?", "Did we find a match?"]
        ).T
    metrics = {
        'Score' : f1,
        'Micro average F1-score' : f1,
        'Micro average recall' : recall,
        'Micro average precision' : precision,
        'Classification report' : classification_report(
            actual_binary,
            predicted_binary
            ),
        'Frequency table of match types' : pd.crosstab(
            df_pairs["Did we find a match?"],
            df_pairs["Do we expect to find the correct match?"]
            )
        }

    return metrics

def evaluate_match_references(
        evaluation_references, match_threshold, 
        length_threshold, sample_N
    ):

    # To get these you want all the matches, regardless of cosine
    match_threshold = -1 

    # Take a random sample of the evaluation references to find matches for
    match_data = evaluation_references.sample(n = sample_N, random_state = 0)
    match_data['Title'] = match_data['title']

    evaluation_references_negative = evaluation_references.loc[
        ~evaluation_references['uber_id'].isin(match_data['uber_id'])
        ]
    
    fuzzy_matcher_positive = FuzzyMatcher(evaluation_references, match_threshold)
    fuzzy_matcher_negative = FuzzyMatcher(evaluation_references_negative, match_threshold)

    predict_match_data_partial = partial(
        predict_match_data,
        match_data=match_data,
        match_threshold=match_threshold,
        length_threshold=length_threshold
        )

    predictions_positive = predict_match_data_partial(fuzzy_matcher_positive)
    predictions_negative = predict_match_data_partial(fuzzy_matcher_negative)

    metrics = evaluate_metric(
        ["Positive"]*sample_N+["Negative"]*sample_N,
        predictions_positive + predictions_negative
        )

    return metrics
