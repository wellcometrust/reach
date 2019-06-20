import pandas as pd

from sklearn.metrics import classification_report, f1_score, recall_score, precision_score

from policytool.refparse.utils import FuzzyMatcher


def get_match_data(evaluation_references, length_threshold, sample_N):

    # To get these you want all the matches, regardless of cosine
    match_threshold = -1 

    # Take a random sample of the evaluation references to find matches for
    references_sample = evaluation_references.sample(n = sample_N, random_state = 0)
    references_sample['Title'] = references_sample['title']

    evaluation_references_negative = evaluation_references.loc[~evaluation_references['uber_id'].isin(references_sample['uber_id'])]
    
    fuzzy_matcher_positive = FuzzyMatcher(evaluation_references, match_threshold)
    fuzzy_matcher_negative = FuzzyMatcher(evaluation_references_negative, match_threshold)

    matched_publication_positive = fuzzy_matcher_positive.match_vectorised(references_sample)
    matched_publication_negative = fuzzy_matcher_negative.match_vectorised(references_sample)

    matched_publication_positive['Title Length'] = [len(title) for title in matched_publication_positive['Title']]
    matched_publication_negative['Title Length'] = [len(title) for title in matched_publication_negative['Title']]

    matched_publication_positive['Match Type'] = ["Positive"]*sample_N
    matched_publication_negative['Match Type'] = ["Negative"]*sample_N

    eval_references = pd.concat([matched_publication_positive, matched_publication_negative])
    eval_references = eval_references[['Title', 'title', 'Cosine_Similarity', 'Match Type', 'Title Length', 'uber_id','Reference id']]

    return eval_references

def predict_match(match, match_threshold, length_threshold):

    if ( 
        (
            match['Cosine_Similarity'] > match_threshold
        ) and 
        (
            match['Title Length'] > length_threshold
        )
        ):
        if match['uber_id'] == match['Reference id']:
            prediction = "Positive - correct match"
        else:
            prediction = "Positive - incorrect match"
    else:
        if match['uber_id'] == match['Reference id']:
            prediction = "Negative - correct match"
        else:
            prediction = "Negative - incorrect match"

    return prediction

def evaluate_metric(actual, predicted):

    actual_binary = ["Positive" if "Positive" in actual_type else "Negative" for actual_type in actual]
    predicted_binary = ["Positive" if "Positive" in pred_type else "Negative" for pred_type in predicted]

    f1 = round(f1_score(actual_binary, predicted_binary, average='micro'), 3)
    recall = round(recall_score(actual_binary, predicted_binary, average='micro'), 3)
    precision = round(precision_score(actual_binary, predicted_binary, average='micro'), 3)

    df_pairs = pd.DataFrame([actual, predicted], index=["Do we expect to find the correct match?", "Did we find a match?"]).T
    metrics = {
        'Score' : f1,
        'Micro average F1-score' : f1,
        'Micro average recall' : recall,
        'Micro average precision' : precision,
        'Classification report' : classification_report(actual_binary, predicted_binary),
        'Frequency table of match types' : pd.crosstab(df_pairs["Did we find a match?"], df_pairs["Do we expect to find the correct match?"])
        }

    return metrics

def evaluate_match_references(evaluation_references, match_threshold, length_threshold, sample_N):

    eval_references = get_match_data(evaluation_references, length_threshold, sample_N)

    predictions = [predict_match(match, match_threshold, length_threshold) for i, match in eval_references.iterrows()]

    metrics = evaluate_metric(eval_references['Match Type'].to_list(), predictions)

    return metrics
