import pandas as pd
import pickle
import sys
from separate import (process_reference_section,
                      summarise_predicted_references,
                      test_get_reference_components)

from predict import predict_references, predict_structure, test_structure


def load_test_files(location, file_dir):
    if location == "s3":
        # Not sure yet
        raise Exception
    elif location == "local":
        # Unstructured references:
        raw_text_data = pd.read_json(file_dir + "/who_iris.json", lines=True)

        # Sample of actual numbers of references for WHO documents:
        actual_number_refs = pd.read_csv(
            file_dir + "/WHO_actual_number_refs_sample.csv"
        )

        # Sample of actual reference structures from WHO documents:
        actual_reference_structures = pd.read_csv(
            file_dir + "/WHO_actual_reference_structures_sample.csv",
            encoding="ISO-8859-1"
        )

        # Model
        with open(file_dir + '/RefSorter_classifier.pkl', 'rb') as f:
            mnb = pickle.load(f)
        with open(file_dir + '/RefSorter_vectorizer.pkl', 'rb') as f:
            vectorizer = pickle.load(f)
    else:
        print("Incorrect location input")
        sys.exit()

    return (raw_text_data, actual_number_refs,
            actual_reference_structures, mnb, vectorizer)


if __name__ == '__main__':

    file_dir = "data"
    location = "local"
    prediction_probability_threshold = 0.75

    (raw_text_data, actual_number_refs,
     actual_reference_structures, mnb, vectorizer) = load_test_files(location,
                                                                     file_dir)

    sample_uri = set(actual_number_refs['uri'])

    raw_text_data_sample = raw_text_data[raw_text_data["uri"].isin(sample_uri)]

    # Predict number of references:
    reference_components = process_reference_section(raw_text_data_sample)

    predicted_number_refs = summarise_predicted_references(
        reference_components,
        raw_text_data_sample
    )

    # How well did it predict the number of references of a sample
    # of actual numbers?
    mean_difference_per, comparison = test_get_reference_components(
        predicted_number_refs,
        actual_number_refs
    )

    # Predict structuring:
    reference_components_predictions = predict_references(
        mnb,
        vectorizer,
        reference_components
    )

    predicted_reference_structures = predict_structure(
        reference_components_predictions,
        prediction_probability_threshold
    )

    # How well did it predict for each category of a reference?
    similarity_score, mean_similarity_score = test_structure(
        predicted_reference_structures,
        actual_reference_structures
    )
