
from sklearn.metrics.pairwise import cosine_similarity
import editdistance
import numpy as np
import pandas as pd

from policytool.refparse.utils.parse import structure_reference

def calc_lev_distance(s1, s2):

    if s1=='' or s2 =='':
        return 0

    return editdistance.eval(s1, s2) / max(len(s1), len(s2))

def get_levenshtein_df(df1, df2):
    """
    Input: two equally sized dataframes
    output: a dataframe of the levenshtein distances between each element pair
    """

    lev_list = [
        calc_lev_distance(a,p) for (a,p) in zip(df1.stack(), df2.stack())
    ]
    lev_dist = pd.DataFrame(
        np.reshape(lev_list, df1.shape),
        columns = df1.columns
    )

    return lev_dist

def evaluate_metric(
        actual_categories, predicted_categories, levenshtein_threshold):

    equal = actual_categories == predicted_categories

    accuracy_cat = equal.mean()
    accuracy = equal.values.mean()

    lev_dist = get_levenshtein_df(actual_categories, predicted_categories)

    quite_equal = lev_dist<levenshtein_threshold
    accuracy_quite_equal_cat = quite_equal.mean()
    accuracy_quite_equal = quite_equal.values.mean()

    number_sample = (actual_categories!="").sum()


    per_cat_metrics = pd.concat([
        number_sample,
        accuracy_cat,
        accuracy_quite_equal_cat,
        lev_dist.mean()
        ], axis = 1)
    per_cat_metrics.columns = [
        'Number of non-blank reference components',
        'Strict accuracy',
        'Lenient accuracy'+
            '(normalised Levenshtein < {})'.format(
                levenshtein_threshold
                ),
        'Mean normalised Levenshtein distance'
        ]

    metrics = {
        'Score' : accuracy,
        'Number of references in sample' : len(actual_categories),
        'Number of non-blank reference components' :\
            number_sample.sum(),
        'Strict accuracy (micro)': accuracy,
        'Lenient accuracy (micro)'+
        '(normalised Levenshtein < {})'.format(
            levenshtein_threshold
            ) : accuracy_quite_equal,
        'Mean normalised Levenshtein distance (all categories)' :\
            lev_dist.mean().mean(),
        'Metrics per category': per_cat_metrics.T
    }

    return {k:round(v,3) for k,v in metrics.items()}

def evaluate_parse(evaluate_parse_data, model, levenshtein_threshold):

    predicted_structure = []
    for reference in evaluate_parse_data['Actual reference']:
        structured_reference = structure_reference(model, reference)
        predicted_structure.append(structured_reference)

    # For the evaluation calculations it's useful for any nan's to be blank strings
    predicted_categories = pd.DataFrame(predicted_structure).replace(np.nan,'').astype(str)
    # Get category names from the predicted categories
    # Important so the actual and predicted are in the same order
    category_names = predicted_categories.columns
    actual_categories = evaluate_parse_data[category_names].replace(np.nan,'').astype(str)

    actual_categories['PubYear'] = [d[0:4] if d!='' else d for d in actual_categories['PubYear']]

    metrics = evaluate_metric(
                    actual_categories,
                    predicted_categories,
                    levenshtein_threshold
                    )

    return metrics
