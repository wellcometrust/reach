
from utils.parse import structure_reference

def evaluate_metric(actual, predicted):

    metric = 50 # Place holder

    return metric

def evaluate_parse(parse_test_data, model):

    predicted_structure = []
    for reference in parse_test_data['Actual reference']:

        structured_reference = structure_reference(model, reference)

        predicted_structure.append(structured_reference)

    parse_test_data['Predicted merged components'] = predicted_structure

    merged_components = {
    'Authors': parse_test_data['Authors'],
    'Journal': parse_test_data['Journal'],
    'Volume': parse_test_data['Volume'],
    'Issue': parse_test_data['Issue'],
    'Pagination': parse_test_data['Pagination'],
    'Title': parse_test_data['Title'],
    'PubYear': parse_test_data['PubYear']
    }

    test_info = parse_test_data
    test_score = evaluate_metric(merged_components, parse_test_data['Predicted merged components'])

    return test_info, test_score