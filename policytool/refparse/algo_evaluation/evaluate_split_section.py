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

def evaluate_splitter_nums(number_predicted_references, number_actual_references, threshold):
    """
    Calculates the number of references test metric for each document.
    Input:
        number_predicted_references : A list of the predicted numbers
                                        of references from a sample of documents
        number_actual_references : A list of the actual numbers
                                        of references from a sample of documents
        threshold : a threshold for the percentage difference acceptable to be below
    Output:
        median_diff : the median percentage difference for a sample of documents
        below_threshold : the percentage of documents with a test metric less than the threshold
    """
   
    doc_metrics = [calc_num_metric(m,n) for m,n in zip(number_predicted_references, number_actual_references)]

    median_diff = round(np.median(doc_metrics), 1)
    below_threshold = round(
        100 * len([x for x in doc_metrics if x <= threshold]) / len(doc_metrics),
        1
    )

    return doc_metrics, median_diff, below_threshold

def evaluate_metric(actual, predicted, sources, threshold):

    doc_metrics, median_diff, below_threshold = evaluate_splitter_nums(predicted, actual, threshold)

    source_metric = pd.DataFrame(
        [list(sources), doc_metrics]
        ).transpose().rename(columns = {0 : "Source", 1 : "Metric"})

    aggregations = {
            'Median difference' : lambda x : round(np.median(x), 1),
            'Percentage below threshold of {}'.format(threshold) : lambda x : round(100 * len([y for y in x if y <= threshold]) / len(x),1)
    }
    grouped_source_metrics = source_metric.groupby('Source')['Metric'].agg(aggregations)

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

    test_scores = evaluate_metric(evaluation_info["Number of references scraped"], evaluation_info["Predicted number of references"], evaluation_info["Source"], threshold)

    return test_scores
