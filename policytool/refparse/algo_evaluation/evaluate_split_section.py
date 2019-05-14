import pandas as pd 
import numpy as np
from utils.split import split_section

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

def evaluate_metric(evaluation_info, threshold):


    evaluation_info['diff_metric'] = [
                                        calc_num_metric(m,n) for m,n in zip(
                                            evaluation_info["Predicted number of references"],
                                            evaluation_info["Number of references scraped"]
                                            )
                                    ]
    median_diff = calc_med_metric(evaluation_info['diff_metric'])
    below_threshold = calc_bel_metric(evaluation_info['diff_metric'], threshold)
    grouped_source_metrics = evaluation_info.groupby('Source')['diff_metric'].agg(
        {'Median difference': lambda x: calc_med_metric(x),
        'Percentage below threshold of {}'.format(threshold) : lambda x : calc_bel_metric(x, threshold)}
        )

    test_scores = {
        'Score' : below_threshold,
        'Percentage below threshold of {}'.format(threshold) : below_threshold,
        'Median difference' : median_diff,
        'Metrics grouped by source' : grouped_source_metrics
        }

    return test_scores

def evaluate_split_section(split_section_test_data, regex, threshold):
    """
    Split the references sections with split_section
    and compare the findings with the ground truth
    """

    evaluation_info = []
    for references_section in split_section_test_data['Reference section']:
        references = split_section(references_section, regex = regex)
        evaluation_info.append(
            {
            "Predicted references" : references,
            "Predicted number of references" : len(references)
            }
            )
    evaluation_info = pd.concat([split_section_test_data, pd.DataFrame(evaluation_info)], axis = 1)

    test_scores = evaluate_metric(evaluation_info, threshold)

    return test_scores
