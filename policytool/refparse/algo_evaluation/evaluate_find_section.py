import sys
sys.path.append("..")
from pdf_parser.pdf_parse import parse_pdf_document, grab_section

import os.path
import pandas as pd
import numpy as np

from sklearn.metrics import classification_report, f1_score
import editdistance

def evaluate_metric_scraped(actual, predicted, section_names):
    """
    Input:
        actual : a boolean list of whether section text was in the pdf
        predicted : a boolean list of whether section text was scraped
        section_names : a list of the section names
    """

    similarity = round(f1_score(actual, predicted, average='micro'), 3)

    test_scores = {
        'Score' : similarity,
        'Micro average F1-score' : similarity,
        'Classification report' : classification_report(actual, predicted) 
        }

    for section_name in set(section_names):
        has_section = [e for i,e in enumerate(actual) if section_names[i] == section_name]
        has_scraped_section = [e for i,e in enumerate(predicted) if section_names[i] == section_name]
        test_scores["Classification report for the {} section".format(section_name)] = classification_report(has_section, has_scraped_section)

    return test_scores


def evaluate_metric_quality(actual, predicted, sections, levenshtein_threshold):
    """
    Text similarity for when there is a section (actual!='')
    """

    section_texts_all = [{'Actual section text' : a, 'Predicted section text' : p, 'Section' : s} for a,p,s in zip(actual, predicted, sections)]

    section_texts_all = list(filter(lambda x: x['Actual section text'] != '', section_texts_all))

    lev_distance = []
    for section_texts in section_texts_all:
        actual_text = section_texts['Actual section text']
        predicted_text = section_texts['Predicted section text']
        lev_distance.append(editdistance.eval(actual_text, predicted_text) / max(len(actual_text), len(predicted_text)))

    # Sections for those that actually exist
    sections_exist = [s['Section'] for s in section_texts_all]

    # Which sections (of the texts that actual exist) were found exactly?
    equal = [l==0 for l in lev_distance]
    
    # Which sections (of the texts that actual exist) were found roughly the same?
    quite_equal = [l<levenshtein_threshold  for l in lev_distance]

    test_scores = {
        'Score' : sum(equal)/len(equal),
        'Mean normalised Levenshtein distance' : np.mean(lev_distance),
        'Strict accuracy (micro)' : sum(equal)/len(equal),
        'Lenient accuracy (micro)' : sum(quite_equal)/len(quite_equal)}

    strict_accuracies = []
    lenient_accuracies = []
    for section_name in set(sections_exist):
        lev_distance_section = [e for i,e in enumerate(lev_distance) if sections_exist[i] == section_name]
        equal_section = [l==0 for l in lev_distance_section]
        quite_equal_section = [l<levenshtein_threshold  for l in lev_distance_section]
        strict_acc_section = sum(equal_section)/len(equal_section)
        lenient_acc_section = sum(quite_equal_section)/len(quite_equal_section)

        test_scores['Mean normalised Levenshtein distance for the {} section'.format(section_name)] = np.mean(lev_distance_section)
        test_scores['Strict accuracy for the {} section'.format(section_name)] = strict_acc_section
        test_scores['Lenient accuracy for the {} section'.format(section_name)] = lenient_acc_section

        strict_accuracies.append(strict_acc_section)
        lenient_accuracies.append(lenient_acc_section)

    test_scores['Strict accuracy (macro)'] = np.mean(strict_accuracies)
    test_scores['Lenient accuracy (macro)'] = np.mean(lenient_accuracies)
    
    return test_scores

def scrape_pdfs(scrape_test_data, scrape_pdf_location):
    """
    Input
    scrape_test_data: A nested dictionary of all the sections text for each pdf in the evaluation data,
                in form {pdf_name1 : {section1 : 'text', section2 : 'text', ... },
                        pdf_name2 : {section1 : 'text', section2 : 'text', ... }, ...}
    Output
    scrape_test_data: the evaluation dataframe now with whether a references section was
        scraped or not, the text scraped for each of the 'sections' sections, and a re-formatted
        actual references section text (in dictionary format)
    """

    # Predict the references text for these pdfs

    sections = scrape_test_data[next(iter(scrape_test_data))].keys()
    text_results = {}
    for pdf_name in scrape_test_data.keys():
        with open('{}/{}.pdf'.format(scrape_pdf_location, pdf_name), 'r') as f:
            pdf_file, full_text = parse_pdf_document(f)
            section_dict = {}
            for section in sections:
                section_text = grab_section(pdf_file, section)
                section_dict.update({section : section_text})
            text_results.update({pdf_name : section_dict})

    return text_results

def evaluate_find_section(scrape_test_data, scrape_pdf_location):
    levenshtein_threshold = 0.3

    text_results = scrape_pdfs(scrape_test_data, scrape_pdf_location)

    section_names = []
    predicted_section = []
    actual_section = []
    for pdf_names in scrape_test_data.keys():
        predicted_sections = text_results[pdf_names]
        actual_sections = scrape_test_data[pdf_names]
        for sections in actual_sections.keys():
            predicted_section.append(predicted_sections[sections])
            actual_section.append(actual_sections[sections])
            section_names.append(sections)

    test1_scores = evaluate_metric_scraped(
        [a!='' for a in actual_section], [p!='' for p in predicted_section],
        section_names
        )

    test2_scores = evaluate_metric_quality(actual_section, predicted_section, section_names, levenshtein_threshold)

    return test1_scores, test2_scores

