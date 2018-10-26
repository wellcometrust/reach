import pandas as pd
import numpy as np

from .test_settings import settings
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from utils import (Predicter, FuzzyMatcher,
                   split_sections, split_reference)


def test_get_reference_components(predicted_number_refs, actual_number_refs):
    """
    Input:
    - How many references found in each document
    - How many references there actually were in a sample of documents
    Output:
    - How much these values match for the sample manually counted
    - This is measured as the average difference as a proportion of the actual
      number
    - The comparison numbers
    """

    print("How well the number of references are predicted being computed...")
    comparison = []
    for index, row in actual_number_refs.iterrows():

        # This will happen when there was a references section pulled only
        # There are a few in the sample who had no references section pulled

        this_document_predicted = predicted_number_refs.loc[
            predicted_number_refs['uri'] == row['uri']
        ].reset_index()

        if (len(this_document_predicted) == 0):
            this_document_predicted = None
            difference_per = None
        else:
            this_document_predicted = this_document_predicted[
                'Predicted number of references'
            ][0]

            if (row['Number of References in WHO pdf'] == 0):
                difference_per = None
            else:
                difference_per = abs(
                    row['Number of References in WHO pdf']
                    - this_document_predicted
                ) / row['Number of References in WHO pdf']

        comparison.append(
            [row['Number of References in WHO pdf'],
             this_document_predicted, difference_per]
        )

    comparison = pd.DataFrame(
        comparison,
        columns=[
            "Number of References in WHO pdf",
            "Predicted number of references",
            "Difference as proportion of actual number"
        ]
    )

    mean_difference_per = np.mean(
        comparison["Difference as proportion of actual number"]
    )

    print(
        "Average difference between actual and predicted number of references",
        "as proportion of actual number is ",
        str(round(mean_difference_per, 4))
    )

    return mean_difference_per, comparison


def split_string(publications, column_name, replace_strings_list=[(',', '.')]):

    publications_column = publications[publications[column_name].notnull()]

    all_column_sentences = []
    for row in publications_column[column_name].astype(str):
        for (char_a, char_b) in replace_strings_list:
            row = row.replace(char_a, char_b)
        for elem in row.split("."):
            all_column_sentences.append(elem)

    target_column = [column_name for i in range(len(all_column_sentences))]

    return all_column_sentences, target_column


def process_training_publications(publications):
    """
    process_training_publications
     to get the structured publications data into a format usable as a
     training set:
     - Input is training set data from a list of classified publications
       (from uber Dimensions, e.g.), make sure it's ok
     - Make list of reference components and which category they fall under
     - Randomly shuffle
    """

    print("Processing publications to be used as training set ...")

    assert 'Authors' in publications, "publications.Authors not defined"
    assert 'Title' in publications, "publications.Title not defined"
    assert 'Journal' in publications, "publications.Journal not defined"
    assert 'PubYear' in publications, "publications.PubYear not defined"
    assert 'Volume' in publications, "publications.Volume not defined"
    assert 'Issue' in publications, "publications.Issue not defined"
    assert 'Pagination' in publications, "publications.Pagination not defined"

    author_sentences, author_target = split_string(publications, 'Authors')
    journal_sentences, journal_target = split_string(publications, 'Journal')
    volume_sentences, volume_target = split_string(publications, 'Volume')
    issue_sentences, issue_target = split_string(publications, 'Issue')
    pagination_sentences, pagination_target = split_string(
        publications,
        'Pagination'
    )
    title_sentences, title_target = split_string(
        publications,
        'Title',
        [(',', '.'), ('?', '?.'), ('!', '!.')]
    )

    # Year is always a float, so no need to separate by full stop
    # Need to convert to string.
    pubyear_publications = publications[publications['PubYear'].notnull()]
    pubyear_sentences = [
        str(int(elem)) for elem in pubyear_publications['PubYear']
    ]
    pubyear_target = ["PubYear" for i in range(len(pubyear_sentences))]

    all_sentences = np.concatenate((
        author_sentences,
        title_sentences,
        journal_sentences,
        pubyear_sentences,
        volume_sentences,
        issue_sentences,
        pagination_sentences), axis=0)

    all_target = np.concatenate((
        author_target,
        title_target,
        journal_target,
        pubyear_target,
        volume_target,
        issue_target,
        pagination_target), axis=0)

    proccessed_publications_dict = {
        'Sentence': all_sentences,
        'Target Classification': all_target
    }

    proccessed_publications = pd.DataFrame(proccessed_publications_dict)
    proccessed_publications = proccessed_publications.sample(
        frac=1
    ).reset_index(drop=True)

    return proccessed_publications


def test_model(mnb, vectorizer, publications_to_test_model):
    test_set = process_training_publications(publications_to_test_model)
    len_test_set = len(test_set)

    count_words_sentences = vectorizer.transform(
        test_set['Sentence']
    ).toarray()
    y_pred = mnb.predict(count_words_sentences)

    mislabeled = np.asarray(test_set['Target Classification']) != y_pred
    num_mislabeled = mislabeled.sum()

    cats_mislabeled = test_set['Target Classification'].loc[mislabeled]
    prop_cats_correct_label = []
    for cats in set(test_set['Target Classification']):
        num_this_cat = len(
            test_set[
                'Target Classification'
            ].loc[test_set['Target Classification'] == cats]
        )

        num_this_cat_mislabelled = len(
            cats_mislabeled.loc[cats_mislabeled == cats])

        prop_cats_correct_label.append(
            [cats, 1 - (num_this_cat_mislabelled/num_this_cat), num_this_cat])

    prop_cats_correct_label = pd.DataFrame(
        prop_cats_correct_label, columns=[
            'Category',
            'Proportion of test set of this category correctly labeled',
            'Number of test set of this category'
        ]
    )

    return num_mislabeled, len_test_set, prop_cats_correct_label


def test_number_refs(raw_text_data, actual_number_refs, organisation_regex,
                     actual_publication_id_name, components_id_name):

    document_ids = actual_number_refs[actual_publication_id_name]

    predicted_number_refs_temp = []

    for document_id in set(document_ids):
        # Get the raw data for this doc id, Should only be one row
        this_document_references = raw_text_data.loc[
            raw_text_data[settings.RAW_PUBLICATION_ID_NAME] == document_id
        ]

        this_document_actual_number = actual_number_refs.loc[
            actual_number_refs[
                actual_publication_id_name
            ] == document_id
        ][settings.NUM_REFS_TITLE_NAME]

        if (len(this_document_actual_number) == 1):
            this_document_actual_number = list(this_document_actual_number)[0]
        else:
            print("More than one actual number of refs for this ID")

        if len(this_document_references) == 1:
            for _, this_doc_reference in this_document_references.iterrows():
                if this_doc_reference["sections"]:
                    references_section = this_doc_reference[
                        "sections"
                    ]["Reference"]
                    references = split_sections(references_section,
                                                organisation_regex)

                    if this_document_actual_number == 0:
                        difference_per = None
                    else:
                        difference_per = abs(
                            this_document_actual_number - len(references)
                            )/this_document_actual_number

                    predicted_number_refs_temp.append([
                        document_id,
                        this_document_actual_number,
                        len(references),
                        difference_per,
                    ])
                else:
                    predicted_number_refs_temp.append([
                        document_id,
                        this_document_actual_number,
                        None,
                        None,
                    ])
        else:
            predicted_number_refs_temp.append([
                document_id,
                this_document_actual_number,
                None,
                None,
            ])
            print("warning: more than one document or none for this id")

    comparison = pd.DataFrame(
        predicted_number_refs_temp, columns=[
            actual_publication_id_name, settings.NUM_REFS_TITLE_NAME,
            'Predicted number of references',
            "Difference as proportion of actual number"
        ])

    mean_difference_per = np.mean(
        comparison["Difference as proportion of actual number"]
    )

    return mean_difference_per, comparison


def test_structure(actual_reference_structures, components_id_name,
                   actual_publication_id_name, mnb, vectorizer):

    category_types = ['Title', 'Authors', 'Journal', 'PubYear',
                      'Volume', 'Issue', 'Pagination']

    similarity_score = []
    raw_reference_components = []
    for _, actual_structure in actual_reference_structures.iterrows():
        # Get the components for this reference and store
        components = split_reference(actual_structure['Actual reference'])
        for component in components:
            raw_reference_components.append({
                'Reference component': component,
                'Reference id': actual_structure['Reference number'],
                'Document uri': actual_structure['Document uri'],
                'Document id': actual_structure[actual_publication_id_name]
            })

    reference_components_ref_structures = pd.DataFrame(
        raw_reference_components)

    predicter = Predicter()

    ref_components_ref_structures_predictions = predicter.predict_references(
        mnb, vectorizer, reference_components_ref_structures)

    predicted_reference_structures = predicter.predict_structure(
        ref_components_ref_structures_predictions,
        settings.PREDICTION_PROBABILITY_THRESHOLD)

    for _, actual_reference in actual_reference_structures.iterrows():
        # Find the predicted reference for this (based on similar title)

        # Get the predicted references from this document
        these_predicted_ref_structures = predicted_reference_structures.loc[
            ((predicted_reference_structures[
                components_id_name
             ] == actual_reference[actual_publication_id_name]) &
             (predicted_reference_structures[
                'Reference id'
             ] == actual_reference['Reference number']
            ))
        ]

        assert len(these_predicted_ref_structures) <= 1, \
            "there is more than 1 predicted ref for this unique doc and ref"

        if len(these_predicted_ref_structures) != 0:
            vectorizer = TfidfVectorizer(lowercase=True, ngram_range=(1, 1))

            # Which categories were there for this predicted reference?
            category_exist = list(set(
                these_predicted_ref_structures.dropna(
                    axis=1, how='all'
                ).columns.values).intersection(set(category_types))
            )

            tfidf_matrix = vectorizer.fit_transform(
                [str(actual_reference[cat]) for cat in category_exist]
            )

            similarity_score_temp = {}
            for cat in category_exist:

                these_predicted_ref_structures_vectors = vectorizer.transform(
                        [str(these_predicted_ref_structures.iloc[0][cat])])

                similarity_score_temp[cat] = list(
                    cosine_similarity(
                        tfidf_matrix,
                        these_predicted_ref_structures_vectors
                    )[0]
                )[0]

        else:
            similarity_score_temp = {}

        similarity_score_temp['Document id'] = actual_reference.get(
            actual_publication_id_name
        )

        similarity_score.append(similarity_score_temp)

    similarity_score = pd.DataFrame(
        similarity_score,
        columns=category_types.extend('Document id')
    )
    mean_similarity_score = similarity_score.mean()

    mean_similarity_score['Number with a prediction'] \
        = similarity_score.count()

    return similarity_score, mean_similarity_score


def test_match(match_publications, test_publications,
               fuzzymatch_threshold, blocksize):

    # How many of test_publications positives match to match_publications?
    # How many of test_publications negatives match to match_publications?

    # Get the data into the same format as would be
    test_publications = test_publications.rename(
        columns={'Match title': 'Title', 'Match pub id': 'Reference id'})

    test_publications['Journal'] = None
    test_publications['PubYear'] = None
    test_publications['Authors'] = None
    test_publications['Issue'] = None
    test_publications['Volume'] = None
    test_publications['Document id'] = range(0, len(test_publications))
    test_publications['Document uri'] = None

    fuzzy_matcher = FuzzyMatcher(
        match_publications,
        fuzzymatch_threshold)

    pos_test_publications = test_publications.loc[
        test_publications['Type'] == "Positive"
    ]

    neg_test_publications = test_publications.loc[
        test_publications['Type'] == "Negative"
    ]

    all_pos_match_data = fuzzy_matcher.fuzzy_match_blocks(
        blocksize,
        pos_test_publications,
        fuzzymatch_threshold)

    all_neg_match_data = fuzzy_matcher.fuzzy_match_blocks(
        blocksize,
        neg_test_publications,
        fuzzymatch_threshold)

    true_positives = all_pos_match_data.loc[
        all_pos_match_data['Reference id'] == all_pos_match_data['WT_Ref_Id']
    ]

    true_negatives = all_pos_match_data.loc[
        all_pos_match_data['Reference id'] != all_pos_match_data['WT_Ref_Id']
    ]

    false_negatives = all_neg_match_data.loc[
        all_neg_match_data['Reference id'] != all_neg_match_data['WT_Ref_Id']
    ]

    false_positives = all_neg_match_data.loc[
        all_neg_match_data['Reference id'] == all_neg_match_data['WT_Ref_Id']
    ]

    return true_positives, true_negatives, false_negatives, false_positives
