import pandas as pd
import numpy as np
import time

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from utils import (predict_references, predict_structure, load_csv_file,
                   load_pickle_file, load_json_file, FuzzyMatcher,
                   split_sections, split_reference)

from settings import settings


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
            raw_text_data[raw_publication_id_name] == document_id
        ]

        this_document_actual_number = actual_number_refs.loc[
            actual_number_refs[
                actual_publication_id_name
            ] == document_id
        ][num_refs_title_name]

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
            actual_publication_id_name, num_refs_title_name,
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

    reference_components_ref_structures_predictions = predict_references(
        mnb, vectorizer, reference_components_ref_structures)

    predicted_reference_structures = predict_structure(
        reference_components_ref_structures_predictions,
        prediction_probability_threshold)

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


if __name__ == '__main__':

    now = time.strftime('%d-%m-%Y %H-%M-%S')

    folder_prefix = "/Users/gallaghe/Code/data-labs/MLReferenceSorter/data"

    pub_data_file_name = ''.join([
        "Publication Year is 2017 ",
        "Funder is WT ",
        "Dimensions-Publication-2018-02-13_11-23-53",
        ".csv",
    ])

    test_pub_data_file_name = "positive_and_negative_publication_samples.csv"

    match_pub_data_file_name = "uber_api_publications.csv"

    num_refs_file_name = "actual_number_refs_sample.csv"
    num_refs_title_name = "Number of References in pdf"

    struct_refs_file_name = "actual_reference_structures_sample.csv"

    test_set_size = 100  # Number of publications to use to test model
    prediction_probability_threshold = 0.75
    test2_thresh = 0.4
    fuzzymatch_sample = 200

    organisations = ['who_iris', 'nice', 'unicef', 'msf']

    # Unstructured references from latest policy scrape:

    raw_publication_id_name = "hash"
    actual_publication_id_name = "hash"
    components_id_name = "Document id"
    actual_uber_id_name = "uber_uber_id"

    log_file = open(
        'Test results - ' + str(now), 'w')
    log_file.write(
        'Organisations = ' + str(organisations) + '\n' +
        'Regexes used = ' + repr(settings._regex_dict) + '\n' +
        'Date of test = ' + str(now) + '\n' +
        'Number of publications in test set = ' + str(test_set_size) + '\n' +
        'WT publication data file name = ' + str(pub_data_file_name) + '\n\n'
        )

    # Load trained model
    mnb = load_pickle_file(settings.MODEL_DIR, settings.CLASSIFIER_FILENAME)
    vectorizer = load_pickle_file(
        settings.MODEL_DIR,
        settings.VECTORIZER_FILENAME
    )

    # Load publication data for testing model predictions
    publications = load_csv_file(
        folder_prefix,
        pub_data_file_name
    )

    # Load manually found number of references for a sample of documents
    actual_number_refs = load_csv_file(
        folder_prefix,
        num_refs_file_name
    )

    # Load manually found structure of references for a sample of documents
    actual_reference_structures = load_csv_file(
        folder_prefix,
        struct_refs_file_name
    )

    # Load WT publications to match references against
    match_publications = load_csv_file(
        folder_prefix,
        match_pub_data_file_name
    )

    test_publications = load_csv_file(
        folder_prefix,
        test_pub_data_file_name
    )

    test1_score = 0
    test2_score = 0
    test3_score = 0
    test4_score = 0

    # TEST 1 : Model predictions =============
    # ========================================
    # How well does the model predict components?
    print("============")
    print("Test 1 - How well does the model predict components?")
    print("============")
    publications_to_test_model = publications.ix[:(test_set_size-1), :]

    num_mislabeled, len_test_set, prop_cats_correct_label = test_model(
        mnb, vectorizer, publications_to_test_model)

    test1_info = str(
        "Number of correctly labelled test points " +
        str(len_test_set-num_mislabeled) + " out of " +
        str(len_test_set) + " = " +
        str(round(100*(len_test_set-num_mislabeled)/len_test_set)) + "%\n" +
        "By category:\n" +
        str(prop_cats_correct_label))

    print(test1_info)

    log_file.write('=====\nTest 1:\n=====\n' + test1_info + "\n\n")

    test1_score = (len_test_set-num_mislabeled)/len_test_set

    # TEST 2 : Number of references ==========
    # ========================================
    # Test how well the number of refs were predicted
    print("============")
    print("Test 2 - How well the number of refs were predicted")
    print("============")

    log_file.write('=====\nTest 2:\n=====\n')

    comparisons = []
    test2_score = {}
    for organisation in organisations:
        print(organisation + "\n-----\n")

        # Just use the data for the relevant source:
        this_actual_number_refs = actual_number_refs.loc[
            actual_number_refs['Source'] == organisation
        ]

        # Select the policy documents which were manually tested
        sample_uri_number_refs = set(
            this_actual_number_refs[actual_publication_id_name]
        )

        # Get the raw data for this organisation:
        raw_text_data = load_json_file(
            settings.SCRAPER_RESULTS_DIR,
            "{}.json".format(organisation)
        )

        # Predict how many references these policy documents have
        raw_text_data_sample_number_refs = raw_text_data[raw_text_data[
            raw_publication_id_name
        ].isin(sample_uri_number_refs)]

        mean_difference_per, comparison = test_number_refs(
            raw_text_data_sample_number_refs,
            this_actual_number_refs,
            settings._regex_dict[organisation],
            actual_publication_id_name,
            components_id_name
        )

        comparison['Source'] = organisation

        number_correct = len(
            comparison.loc[
                comparison[
                    'Difference as proportion of actual number'
                ] <= test2_thresh
            ]
        )

        test2_info = str(
            "Average difference between actual and predicted number of " +
            "references as proportion of actual number is " +
            str(round(mean_difference_per, 4)) + "\n" +
            "Proportion of test references with close to the same " +
            "actual and predicted number of references (difference <= " +
            str(test2_thresh) + ") = " +
            str(round(number_correct/len(comparison), 4)))
        print(test2_info)

        log_file.write(organisation + "\n-----\n" + test2_info + "\n\n")

        test2_score[organisation] = number_correct/len(comparison)
        comparisons.append(comparison)

    comparisons = pd.concat(comparisons)
    comparisons.to_csv(
        "Test results - number of references comparison - " + now + ".csv"
    )

    # TEST 3 : Structuring of references ==========
    # ========================================
    # Test how well a title was predicted in a reference
    print("============")
    print(
        "Test 3 - How well reference components were predicted in a reference"
    )
    print("============")

    log_file.write('=====\nTest 3:\n=====\n')

    similarity_scores = []
    test3_score = {}

    for organisation in organisations:
        print(organisation + "\n-----\n")

        # Just use the data for the relevant source:
        this_actual_reference_structures = actual_reference_structures.loc[
            actual_reference_structures['Source'] == organisation
        ]

        # How well did it predict for each category of a reference?
        similarity_score, mean_similarity_score = test_structure(
            this_actual_reference_structures,
            components_id_name,
            actual_publication_id_name,
            mnb, vectorizer)

        test3_info = "".join([
            "Average similarity scores between predicted and actual ",
            "references for each component, using a sample of ",
            "{} references: \n".format(len(this_actual_reference_structures)),
            "{}\n".format(mean_similarity_score),
            "Number of samples with predictions: ",
            str(mean_similarity_score['Number with a prediction']),
        ])
        print(test3_info)

        log_file.write(organisation + "\n-----\n" + test3_info + "\n\n")

        test3_score[organisation] = mean_similarity_score['Title']
        print(similarity_score)

        similarity_scores.append(similarity_score)

    similarity_scores = pd.concat(similarity_scores)
    similarity_scores.to_csv(
        "Test results - cosine similarity of references comparison - "
        + now
        + ".csv"
    )

    # TEST 4 : Fuzzy matching of references ==========
    # ========================================
    print("============")
    print(
        "Test 4 - How well the algo matches list references with WT references"
    )
    print("===========")

    # Take the negative examples out of the match publications:
    neg_test_pub_ids = test_publications.loc[
        test_publications['Type'] == 'Negative'
    ]['Match pub id']

    match_publications = match_publications.loc[
        ~match_publications['uber_id'].isin(neg_test_pub_ids)
    ].reset_index()

    (true_positives, true_negatives,
     false_negatives, false_positives) = test_match(
        match_publications,
        test_publications,
        settings.FUZZYMATCH_THRESHOLD,
        settings.BLOCKSIZE
    )

    num_pos = sum(test_publications['Type'] == 'Positive')
    num_neg = sum(test_publications['Type'] == 'Negative')

    proportion_correct_match = (
        len(true_positives) + (num_neg - len(false_negatives))
    )/(num_pos + num_neg)

    test4_info = """Proportion correctly matched from a random sample of
    {pos} positive and {neg} negative samples: {correct}

    Number from positive set with a match with the same ID: {true_pos}
    Number from positive set with a match with a different ID: {true_neg}
    Number from negative set with a match with a different ID: {false_pos}
    Number from negative set with a match with the same ID: {false_neg}
    Number from negative set with no matches: {no_match}
    """.format(
        pos=num_pos,
        neg=num_neg,
        correct=proportion_correct_match,
        true_pos=len(true_positives),
        true_neg=len(false_negatives),
        false_pos=len(false_positives),
        false_neg=len(false_positives),
        no_match=num_neg - len(false_negatives) - len(false_positives),
    )

    true_negatives['Type'] = "Positive set with match with a different ID"
    false_negatives['Type'] = "Negative set with a match"

    print(test4_info)

    pd.concat([true_negatives, false_negatives]).to_csv(
        "Test results - False matches - " + now + ".csv")

    log_file.write('=====\nTest 4:\n=====\n' + test4_info)

    test4_score = proportion_correct_match

    # Summary
    # ========================================
    print("============")
    print("Summary")
    print("===========")

    tests_weightings = [1, 1, 1, 1]

    print(test1_score)
    print(test2_score)
    print(test2_score['who_iris'])
    print(test3_score['who_iris'])
    print(test4_score)

    overall_scores = []
    for org in organisations:
        overall_scores.append(
            {org: test1_score*test2_score[org]*test3_score[org]*test4_score})

    summary_info = str(
        "Test 1 = " + str(test1_score) + '\n' +
        "Test 2 = " + str(test2_score) + '\n' +
        "Test 3 = " + str(test3_score) + '\n' +
        "Test 4 = " + str(test4_score) + '\n' +
        "Overall score = " + str(overall_scores))
    print(summary_info)

    log_file.write("=====\nSummary:\n=====\n" + summary_info)

    log_file.close()
