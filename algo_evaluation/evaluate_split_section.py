import pandas as pd
from utils.split import split_section

def evaluate_metric(actual, predicted):

    test_scores = {'Score' : 50, 'More info' : "More information about this test"}

    return test_scores

def evaluate_split_section(split_section_test_data, regex, threshold):
    """
    Split the references sections with split_section
    and compare the findings with the ground truth
    """

    comparison = []
    for references_section in split_section_test_data['Reference section']:
        references = split_section(references_section, regex = regex)

        comparison.append(
            {
            "Predicted references" : references,
            "Predicted number of references" : len(references)
            }
            )
    comparison = pd.concat([split_section_test_data, pd.DataFrame(comparison)], axis = 1)

    test_info = comparison
    test_scores = evaluate_metric(comparison["Number of references scraped"], comparison["Predicted number of references"])

    return test_scores 
