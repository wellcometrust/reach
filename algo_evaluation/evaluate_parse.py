
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

    test_info = parse_test_data
    test_score = evaluate_metric(parse_test_data['Title'], parse_test_data['Predicted merged components'])

    return test_info, test_score