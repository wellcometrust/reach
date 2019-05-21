from sklearn.metrics import classification_report, f1_score, confusion_matrix
import editdistance
import pandas as pd
import numpy as np

import os.path
import sys

sys.path.append("..")
from pdf_parser.pdf_parse import parse_pdf_document, grab_section


def pretty_confusion_matrix(actual_data, predict_data, labels):
    cm  = confusion_matrix(actual_data, predict_data, labels = labels)
    pretty_conf = pd.DataFrame(
        cm,
        columns=["Predicted {}".format(label) for label in labels],
        index=["Actually {}".format(label) for label in labels]
        )
    return pretty_conf

def evaluate_metric_scraped(actual, predicted, sections):
    """
    Input:
        actual : a boolean list of whether section text was in the pdf
        predicted : a boolean list of whether section text was scraped
        sections : a list of the section names for each actual/predicted pair
    Output:
        Various metrics for how accurately the scraper scraped a
        section or not, no comment on how good the scrape was though
    """

    similarity = round(f1_score(actual, predicted, average='micro'), 3)

    test_scores = {
        'Score' : similarity,
        'Micro average F1-score' : similarity,
        'Classification report' : classification_report(actual, predicted),
        'Confusion matrix' : pretty_confusion_matrix(
                actual, predicted, [True, False]
            )
        }

    for section_name in set(sections):
        actual_section = [
            a for (s,a) in zip(sections, actual) if s == section_name
        ]
        predicted_section = [
            p for (s,p) in zip(sections, predicted) if s == section_name
        ]
        test_scores["Classification report for the {} section".format(
            section_name
            )] = classification_report(actual_section, predicted_section)
        test_scores["Confusion matrix for the {} section".format(
            section_name
            )] = pretty_confusion_matrix(
                    actual_section, predicted_section, [True, False]
                )

    return test_scores


def evaluate_metric_quality(scrape_data, levenshtein_threshold):
    """
    Normalised Levenshtein distances between actual and predicted section text
    for pdfs where there is a section (actual!='')
    """

    # Get rid of times when there is no section
    scrape_data = list(filter(lambda x: x['Actual text'] != '', scrape_data))

    actual_texts = [s['Actual text'] for s in scrape_data]
    predicted_texts = [s['Predicted text'] for s in scrape_data]
    sections = [s['Section'] for s in scrape_data]

    # Get all the normalised Lev distances
    lev_distances = [
        editdistance.eval(actual_text, predicted_text) / 
        max(len(actual_text), len(predicted_text)) \
        for (actual_text, predicted_text) in 
            zip(actual_texts, predicted_texts)
    ]   

    # Which sections were found exactly?
    equal = [lev_distance == 0 for lev_distance in lev_distances]
    
    # Which sections were found roughly the same?
    quite_equal = [
        lev_distance<levenshtein_threshold  for lev_distance in lev_distances
    ]

    test_scores = {
        'Score' : np.mean(equal),
        'Mean normalised Levenshtein distance' : np.mean(lev_distances),
        'Strict accuracy (micro)' : np.mean(equal),
        'Lenient accuracy (micro)' : np.mean(quite_equal)}

    for section_name in set(sections):
        # Get the Levenshtein distances for this sections actual-predicted pairs
        lev_distances_section = [
                lev_distance for (section,lev_distance) \
                in zip(sections, lev_distances) \
                if section == section_name
            ]

        equal_section = [l==0 for l in lev_distances_section]
        quite_equal_section = [
            l<levenshtein_threshold  for l in lev_distances_section
        ]
        strict_acc_section = np.mean(equal_section)
        lenient_acc_section = np.mean(quite_equal_section)

        test_scores[
            'Mean normalised Levenshtein distance for the {} section'.format(
                section_name
                )
            ] = np.mean(lev_distances_section)
        test_scores[
            'Strict accuracy for the {} section'.format(section_name)
            ] = strict_acc_section
        test_scores[
            'Lenient accuracy for the {} section'.format(section_name)
            ] = lenient_acc_section
    
    return test_scores

def scrape_process_pdf(
        section_names, pdf_name, scrape_pdf_location, actual_texts
        ):
    """
    Input:
        section_names :  the list of sections we are looking for in the pdf
        pdf_name : the name of the pdf
        scrape_pdf_location : the file location of the pdf
    Output:
        scrape_data : a list of dicts with the predicted and actual texts for
            each of the sections we looked for in the pdf
    """
    with open('{}/{}.pdf'.format(scrape_pdf_location, pdf_name), 'r') as f:
        pdf_file, full_text = parse_pdf_document(f)
        scrape_data = []
        for section_name in section_names:
            scrape_data.append({
                'File' : pdf_name,
                'Section' : section_name,
                'Predicted text' : grab_section(pdf_file, section_name),
                'Actual text' : actual_texts[section_name]})
    return scrape_data


def evaluate_find_section(
        evaluate_find_section_data, scrape_pdf_location, levenshtein_threshold
        ):

    # Get the predicted text for each of the pdf sections for each pdf
    section_names = evaluate_find_section_data[
        next(iter(evaluate_find_section_data))
        ].keys()
    scrape_data = []
    for pdf_name, actual_texts in evaluate_find_section_data.items():
        scrape_data.extend(
            scrape_process_pdf(section_names, pdf_name, scrape_pdf_location, actual_texts)
            ) 

    test1_scores = evaluate_metric_scraped(
        [pred_section['Actual text']!='' for pred_section in scrape_data],
        [pred_section['Predicted text']!='' for pred_section in scrape_data],
        [pred_section['Section'] for pred_section in scrape_data]
        )

    test2_scores = evaluate_metric_quality(
        scrape_data,
        levenshtein_threshold)

    return test1_scores, test2_scores

