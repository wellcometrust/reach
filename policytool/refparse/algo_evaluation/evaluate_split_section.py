import pandas as pd 
import numpy as np
from policytool.refparse.utils.split import split_section

def calc_num_metric(predicted_number, actual_number):
    """
    How similar are 2 numbers of references?
    The difference between the predicted and actual numbers of references
    as a percentage of the actual number
    """

    # In the case of 0 references (some documents don't have references but do
    # have a reference section), set actual_number to the closest integer, 1.
    # This introduces some small error, but avoids the script throwing a math error
    if actual_number == 0:
        actual_number = 1

    metric = abs(100*((predicted_number - actual_number) / actual_number))

    return metric

def calc_med_metric(metrics):

    med_metric = round(np.median(metrics), 1)

    return med_metric

def calc_bel_metric(metrics, threshold):

    bel_metric = round(
        100 * len([x for x in metrics if x <= threshold]) / len(metrics),
        1
    )

    return bel_metric

def evaluate_metrics(actual_pred_num_references, threshold):


    actual_pred_num_references['diff_metric'] = [
        calc_num_metric(m,n) for m,n in zip(
            actual_pred_num_references["Predicted number of references"],
            actual_pred_num_references["Number of references scraped"]
        )
    ]

    median_diff = calc_med_metric(actual_pred_num_references['diff_metric'])
    below_threshold = calc_bel_metric(actual_pred_num_references['diff_metric'], threshold)
    grouped_source_metrics = actual_pred_num_references.groupby('Source')['diff_metric'].agg({
        'Number of reference sections in sample': lambda x: len(x),
        'Median difference': lambda x: calc_med_metric(x),
        'Percentage below threshold of {}'.format(threshold) : lambda x : calc_bel_metric(x, threshold)
    })

    metrics = {
        'Score' : below_threshold,
        'Number of reference sections in sample' : len(actual_pred_num_references),
        'Percentage below threshold of {}'.format(threshold) : below_threshold,
        'Median difference' : median_diff,
        'Metrics grouped by source' : grouped_source_metrics.T
        }

    return metrics

def evaluate_split_section(evaluate_split_section_data, regex, threshold):
    """
    Split the references sections with split_section
    and compare the findings with the ground truth
    """

    actual_pred_num_references = []
    for references_section in evaluate_split_section_data['Reference section']:
        references = split_section(references_section, regex = regex)
        actual_pred_num_references.append({
            "Predicted references" : references,
            "Predicted number of references" : len(references)
        })
    actual_pred_num_references = pd.concat([evaluate_split_section_data, pd.DataFrame(actual_pred_num_references)], axis = 1)

    metrics = evaluate_metrics(actual_pred_num_references, threshold)

    return metrics
