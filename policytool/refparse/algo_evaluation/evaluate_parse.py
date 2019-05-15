
import pandas as pd
import numpy as np
import editdistance

from utils.parse import structure_reference
from sklearn.metrics.pairwise import cosine_similarity

def get_levenshtein_df(df1, df2):
    """
    Input: two equally sized dataframes
    output: a dataframe of the levenshtein distances between each element pair
    """

    calc_lev_dist_column = lambda s1, s2: editdistance.eval(s1, s2)/max(len(s1), len(s2)) if (s1!='' or s2 !='') else 0
    lev_dist = pd.DataFrame([df1[column].combine(df2[column], calc_lev_dist_column) for column in df1.columns]).T

    return lev_dist

def evaluate_metric(actual_components_list, predicted_components_list, levenshtein_threshold):

    # For the computations below it's useful for any nan's to be blank strings
    df1 = pd.DataFrame(actual_components_list).replace(np.nan,'').astype(str)
    df2 = pd.DataFrame(predicted_components_list).replace(np.nan,'').astype(str)

    df1['PubYear'] = [d[0:4] if d!='' else d for d in df1['PubYear']]

    equal = df1 == df2

    proportion_equal_cat = equal.sum()/len(equal)
    proportion_equal = (equal.sum().sum())/(equal.shape[0]*equal.shape[1])

    lev_dist = get_levenshtein_df(df1, df2)

    quite_equal = lev_dist<levenshtein_threshold
    proportion_quite_equal_cat = quite_equal.sum()/len(quite_equal)
    proportion_quite_equal = (quite_equal.sum().sum())/(quite_equal.shape[0]*quite_equal.shape[1])

    test_scores = {
            'Score' : proportion_equal,
            'Proportion of components predicted correctly (macro)' : proportion_equal,
            'Proportion of components predicted correctly (micro)' : proportion_equal_cat,
            'Mean normalised Levenshtein distance (macro)' : lev_dist.mean().mean(),
            'Mean normalised Levenshtein distance (micro)' : lev_dist.mean(),
            'Proportion of components predicted almost correctly (normalised Levenshtein < {}) (macro)'.format(levenshtein_threshold) : proportion_quite_equal,
            'Proportion of components predicted almost correctly (normalised Levenshtein < {}) (micro)'.format(levenshtein_threshold) : proportion_quite_equal_cat
            }

    return test_scores

def evaluate_parse(parse_test_data, model, levenshtein_threshold):

    predicted_structure = []
    for reference in parse_test_data['Actual reference']:
        structured_reference = structure_reference(model, reference)
        predicted_structure.append(structured_reference)

    parse_test_data['Predicted merged components'] = predicted_structure

    component_names = ['Authors', 'Journal', 'Volume', 'Issue', 'Pagination', 'Title', 'PubYear']
    actual_components_list = []
    for _,reference_test_data in parse_test_data.iterrows():
        a = {}
        for component_name in component_names:
            a.update({component_name : reference_test_data[component_name]})
        actual_components_list.append(a)

    test_scores = evaluate_metric(actual_components_list, parse_test_data['Predicted merged components'].tolist(), levenshtein_threshold)

    return test_scores