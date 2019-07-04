import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from datetime import datetime
import os

from sklearn.metrics import (
    f1_score, recall_score, precision_score
    )

from policytool.refparse.evaluate_algo import yield_pubs_json
from policytool.refparse.utils import FuzzyMatcher

def get_matches(evaluation_references, sample_N):

    # Take a random sample of the evaluation references to find matches for
    match_data = evaluation_references.sample(n = sample_N*2, random_state = 0).reset_index() 
    match_data['Title'] = match_data['title']

    match_data_positive = match_data.iloc[0:sample_N]
    match_data_negative = match_data.iloc[sample_N:]

    evaluation_references_without_negative = evaluation_references.loc[
        ~evaluation_references['uber_id'].isin(match_data_negative['uber_id'])
        ]

    fuzzy_matcher = FuzzyMatcher(evaluation_references_without_negative, -1)

    match_data_pos_neg = pd.concat([match_data_positive, match_data_negative])
    eval_references = pd.DataFrame()
    for i, ref in match_data_pos_neg.iterrows():
        eval_references = pd.concat([eval_references, fuzzy_matcher.match_vectorised(ref)])

    eval_references["Title Length"] = [len(title) for title in eval_references["Title"]]
    eval_references["Match Type"] = ["Positive"]*sample_N + ["Negative"]*sample_N

    return eval_references

def print_percentiles(data, percentile, data_description):

    perc = np.percentile(data, percentile) 
    print("{}th percentile for the {} = {}".format(
        percentile,
        data_description,
        round(perc, 2)
        )
    )

def make_neg_pos_plots(eval_references, now):

    negative_matches = eval_references[
        eval_references['Match Type']=="Negative"
    ]
    true_positive_matches = eval_references[
        (eval_references['Match Type']=="Positive") &
        (eval_references['uber_id']==eval_references['Reference id'])
    ]
    false_positive_matches = eval_references[
        (eval_references['Match Type']=="Positive") &
        (eval_references['uber_id']!=eval_references['Reference id'])    
    ]

    N = len(eval_references)/2

    print("Number of references correctly matched with positive set (true positives):\
        {} out of {}".format(len(true_positive_matches), N))
    print("Number of references incorrectly matched with positive set (false positives):\
        {} out of {}".format(len(false_positive_matches), N))
    print("Number of references in negative set:\
        {}".format(len(negative_matches)))

    print_percentiles(
        negative_matches['Cosine_Similarity'], 95,
        "cosine similarities of the negative set"
    ) # Get rid of most of the TN

    print_percentiles(
        true_positive_matches['Title Length'], 5,
        "title lengths of the true positives"
    ) # Don't loose too many of the TP


    print_percentiles(
        negative_matches['Cosine_Similarity'], 99,
        "cosine similarities of the negative set"
    ) # Get rid of most of the TN

    print_percentiles(
        true_positive_matches['Title Length'], 1,
        "title lengths of the true positives"
    ) # Don't loose too many of the TP

    figure_path = "negative_cosines_hist_{:%Y-%m-%d-%H%M}.png".format(now)
    fig, ax1 = plt.subplots(figsize=(10,5))
    ax1.set_title('Cosine similarities of the negative matches')
    ax1.set_xlabel('Cosine Similarity')
    ax1.set_ylabel('Frequency')
    ax1.set_xlim([0,1])
    plt.hist(
        negative_matches['Cosine_Similarity'].to_list(),
        density=True, bins = 50, color = "r", alpha = 0.75
    )
    plt.savefig(figure_path) 

    figure_path = "negative_cosines_len_scatter_{:%Y-%m-%d-%H%M}.png"\
        .format(now)
    fig, ax1 = plt.subplots(figsize=(6,6))
    ax1.set_title('Cosine similarities vs title length\n\
        of negative matches')
    ax1.set_xlabel('Title length')
    ax1.set_ylabel('Cosine Similarity')
    plt.scatter(
        [len(title) for title in negative_matches['Title']],
        negative_matches['Cosine_Similarity'].to_list(),
        color = "r", alpha =0.5
    )
    plt.savefig(figure_path) 

    figure_path = "title_lengths_{:%Y-%m-%d-%H%M}.png".format(now)
    fig, ax1 = plt.subplots(figsize=(10,5))
    ax1.set_title('Title lengths true and false positives')
    ax1.set_xlabel('Title length')
    ax1.set_ylabel('Frequency')
    plt.hist(
        [len(title) for title in true_positive_matches['Title']],
        density=True, bins = 50, color = "g", alpha = 0.75
    )
    plt.hist(
        [len(title) for title in false_positive_matches['Title']],
        density=True, bins = 20, color = "m", alpha = 0.75
    )
    plt.legend(
        labels=(
            'Correctly matched titles (true positives)',
            'Incorrectly matched titles (false positives)'
            )
    )
    plt.savefig(figure_path) 


def get_predict_result(match, cosine_threshold, length_threshold):

    if (
        match['Cosine_Similarity'] > cosine_threshold and 
        match['Title Length'] > length_threshold
    ):
        prediction = "Positive"
    else:
        prediction = "Negative"

    return prediction


def make_heat_plots(match_scores, colour_var_name, now):

    match_scores_df = pd.DataFrame(match_scores).round(4)

    data_pivoted = match_scores_df.pivot(
        "Match threshold", "Length threshold", colour_var_name
        ).sort_values(
            by = ['Match threshold'],
            ascending = False
        )
    figure_path = "thresholds_{}_negative_heatmap_\
        {:%Y-%m-%d-%H%M}.png".format(colour_var_name, now)
    fig, ax1 = plt.subplots(figsize=(8,7))
    ax1.set_title(
        'F1 scores for different thresholds'
    )
    sns.heatmap(data_pivoted, cbar_kws={'label': colour_var_name}) # annot = True, 
    plt.savefig(figure_path)

if __name__ == '__main__':

    EVAL_PUB_DATA_FILE_NAME = "epmc-metadata.json"
    FOLDER_PREFIX = "../data_evaluate"

    empc_file = os.path.join(
        os.path.dirname('__main__'),
        FOLDER_PREFIX, EVAL_PUB_DATA_FILE_NAME
        )
    total_N = 100000
    sample_N = 10000

    print("===== Loading {} lines of the EMPC data".format(total_N),
        "and getting match evaluation data for",
        "a random {} of these =====".format(sample_N)
        )
    evaluation_references = [p for p in yield_pubs_json(
        empc_file, total_N
        )
    ]
    evaluation_references = pd.DataFrame(evaluation_references)

    eval_references = get_matches(evaluation_references, sample_N)

    now = datetime.now()
    make_neg_pos_plots(
        eval_references,
        now
    )

    print("===== Running match predictions for different thresholds =====")
    match_scores = []
    for cosine_threshold in np.linspace(0.5, 1, 10, endpoint=True):
        for length_threshold in  np.arange(0, 150, 5):
            predictions = [
                get_predict_result(
                    match, cosine_threshold, length_threshold
                ) for i, match in eval_references.iterrows()
            ]
            actual = eval_references['Match Type'].to_list()
            f1 = round(f1_score(actual, predictions, average='micro'), 3)
            recall = round(recall_score(
                actual, predictions,
                average='binary',
                pos_label = "Negative"
                ), 3)
            precision = round(precision_score(
                actual, predictions,
                average='binary',
                pos_label = "Positive"
                ), 3)

            match_scores.append(
                {'Match threshold' : cosine_threshold,
                'Length threshold' : length_threshold,
                'F1 Score' : f1,
                'Recall' : recall,
                'Precision' : precision
                })
        print(cosine_threshold)

    make_heat_plots(match_scores, "F1 Score", now)
    make_heat_plots(match_scores, "Recall", now)
    make_heat_plots(match_scores, "Precision", now)

