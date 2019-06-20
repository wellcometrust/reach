import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os

from sklearn.metrics import (
    f1_score, recall_score, precision_score
    )
from policytool.refparse.algo_evaluation.evaluate_match_references\
    import get_match_data

from policytool.refparse.evaluate_algo import load_pubs_json

def get_predict_result(match, cosine_threshold, length_threshold):

    if ( 
        (
            match['Cosine_Similarity'] > cosine_threshold
        ) and 
        (
            match['Title Length'] > length_threshold
        )
        ):
        prediction = "Positive"
    else:
        prediction = "Negative"

    return prediction


def make_neg_pos_plots(
        matched_pubs_negative,
        matched_pubs_positive,
        incorrect_matched_pubs_positive,
        N,
        now
        ):

    print("Number of references correctly matched with positive set:\
        {} out of {}".format(len(matched_pubs_positive), N))
    print("Number of references incorrectly matched with positive set:\
        {} out of {}".format(len(incorrect_matched_pubs_positive), N))
    print("Number of references in negative set:\
        {}".format(len(matched_pubs_negative)))

    figure_path = "negative_cosines_hist_{:%Y-%m-%d-%H%M}.png".format(now)
    fig, ax1 = plt.subplots(figsize=(10,5))
    ax1.set_title('Cosine similarities of matches in the negative set')
    ax1.set_xlabel('Cosine Similarity')
    ax1.set_ylabel('Frequency')
    ax1.set_xlim([0,1])
    plt.hist(
        matched_pubs_negative['Cosine_Similarity'].to_list(),
        density=True, bins = 50, color = "r", alpha = 0.75
    )
    plt.savefig(figure_path) 

    figure_path = "negative_cosines_len_scatter_{:%Y-%m-%d-%H%M}.png"\
        .format(now)
    fig, ax1 = plt.subplots(figsize=(6,6))
    ax1.set_title('Cosine similarities vs title length\n\
        of matches in the negative set')
    ax1.set_xlabel('Title length')
    ax1.set_ylabel('Cosine Similarity')
    plt.scatter(
        [len(title) for title in matched_pubs_negative['Title']],
        matched_pubs_negative['Cosine_Similarity'].to_list(),
        color = "r", alpha =0.5
    )
    plt.savefig(figure_path) 

    figure_path = "title_lengths_{:%Y-%m-%d-%H%M}.png".format(now)
    fig, ax1 = plt.subplots(figsize=(10,5))
    ax1.set_title('Title lengths when correctly and incorrectly\
        matched with the positive set')
    ax1.set_xlabel('Title length')
    ax1.set_ylabel('Frequency')
    plt.hist(
        [len(title) for title in matched_pubs_positive['Title']],
        density=True, bins = 50, color = "g", alpha = 0.75
    )
    plt.hist(
        [len(title) for title in incorrect_matched_pubs_positive['Title']],
        density=True, bins = 20, color = "m", alpha = 0.75
    )
    plt.legend(
        labels=('Correctly matched titles', 'Incorrectly matched titles')
    )
    plt.savefig(figure_path) 

def make_heat_plots(match_scores_df, colour_var_name, now):

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


def print_percentiles(data, percentile, data_description):

    perc = np.percentile(data, percentile) 
    print("{}th percentile for the {} = {}".format(
        percentile,
        data_description,
        round(perc, 2)
        )
    )

if __name__ == '__main__':

    EVAL_PUB_DATA_FILE_NAME = "epmc-metadata.json"
    FOLDER_PREFIX = "../data_evaluate"

    empc_file = os.path.join(FOLDER_PREFIX, EVAL_PUB_DATA_FILE_NAME)
    total_N = 100000
    sample_N = 10000

    print("===== Loading {} lines of the EMPC data".format(total_N),
        "and getting match evaluation data for",
        "a random {} of these =====".format(sample_N)
        )
    evaluation_references = load_pubs_json(empc_file, total_N)
    length_threshold = -1 # Effectively no threshold
    eval_references = get_match_data(
        evaluation_references,
        length_threshold,
        sample_N
    )

    matched_pubs_negative = eval_references[
        eval_references['Match Type']=="Negative"
    ]
    matched_pubs_positive = eval_references[
        (
            (eval_references['Match Type']=="Positive") &
            (eval_references['uber_id']==eval_references['Reference id'])
        )
    ]
    incorrect_matched_pubs_positive = eval_references[
        (
            (eval_references['Match Type']=="Positive") &
            (eval_references['uber_id']!=eval_references['Reference id'])
        )
    ]

    now = datetime.now()
    make_neg_pos_plots(
        matched_pubs_negative,
        matched_pubs_positive,
        incorrect_matched_pubs_positive,
        len(eval_references)/2,
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
            f1 = round(f1_score(
                eval_references['Match Type'].to_list(),
                predictions,
                average='micro'
                ), 3)
            recall = round(recall_score(
                eval_references['Match Type'].to_list(),
                predictions,
                average='binary',
                pos_label = "Negative"
                ), 3)
            precision = round(precision_score(
                eval_references['Match Type'].to_list(),
                predictions,
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

    match_scores_df = pd.DataFrame(match_scores).round(4)
    
    make_heat_plots(match_scores_df, "F1 Score", now)
    make_heat_plots(match_scores_df, "Recall", now)
    make_heat_plots(match_scores_df, "Precision", now)

    print_percentiles(
        matched_pubs_negative['Cosine_Similarity'],
        95,
        "cosine similarities of the negative set"
    ) # Get rid of most of the TN

    print_percentiles(
        matched_pubs_positive['Title Length'],
        5,
        "title lengths of the correctly matched positive set"
    ) # Don't loose too many of the TP

