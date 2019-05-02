import pandas as pd
from utils.split import split_section

def test_metric(actual, predicted):

    metric = 50 # Place holder

    return metric

def test_split_section(split_section_test_data):
    """
    Split the references sections with split_section
    and compare the findings with the ground truth
    """

    comparison = []
    for references_section in split_section_test_data['Reference section']:
        references = split_section(references_section)

        comparison.append(
            {
            "Predicted references" : references,
            "Predicted number of references" : len(references)
            }
            )
    comparison = pd.concat([split_section_test_data, pd.DataFrame(comparison)], axis = 1)

    test_info = comparison
    test_score = test_metric(comparison["Number of references scraped"], comparison["Predicted number of references"])

    return test_info, test_score