from sklearn.metrics import classification_report, f1_score, confusion_matrix
import editdistance
import pandas as pd
import numpy as np

import os.path
import sys

from policytool.pdf_parser.pdf_parse import parse_pdf_document, grab_section


def pretty_confusion_matrix(actual_data, predict_data, labels):
    cm  = confusion_matrix(actual_data, predict_data, labels = labels)
    pretty_conf = pd.DataFrame(
        cm,
        columns=["Predicted {}".format(label) for label in labels],
        index=["Actually {}".format(label) for label in labels]
        )
    return pretty_conf

def evaluate_metric_scraped(actual, predicted, sections, files, providers):
    """
    Input:
        actual : a boolean list of whether section text was in the pdf
        predicted : a boolean list of whether section text was scraped
        sections : a list of the section names for each actual/predicted pair
        files : a list of the pdf names
        providers : a list of the providers where each pdf came from
    Output:
        Various metrics for how accurately the scraper scraped a
        section or not, no comment on how good the scrape was though
    """

    similarity = round(f1_score(actual, predicted, average='micro'), 3)

    combined_data = pd.DataFrame({
        'Actual' : actual,
        'Predicted' : predicted,
        'Section' : sections,
        'Files' : files, 
        'Provider' : providers
        })

    all_providers = list(set(providers))

    get_num_pdfs = lambda x: len(x["Files"].unique())
    get_num_pdfs_text = lambda x: len(x[x["Actual"]==True]["Files"].unique())
    get_prop_text = lambda x: round(sum(x["Actual"]==True) / len(x), 3)
    get_f1 = lambda x: round(
        f1_score(
            list(x["Actual"]),
            list(x["Predicted"]),
            average='micro'
            ),
        3
        )
    
    grouped_provider = combined_data.groupby("Provider")

    n_by_prov = grouped_provider.apply(get_num_pdfs)
    n_text_by_prov = grouped_provider.apply(get_num_pdfs_text)
    prop_text_by_prov = round(n_text_by_prov/n_by_prov, 3)
    f1_by_prov = grouped_provider.apply(get_f1)

    grouped_provider_section = combined_data.groupby(["Provider","Section"])

    n_text_by_sect = grouped_provider_section.apply(get_num_pdfs_text)
    prop_text_by_sect = grouped_provider_section.apply(get_prop_text)
    f1_by_sect = grouped_provider_section.apply(get_f1)

    metrics_by_prov = pd.concat(
        [n_by_prov, n_text_by_prov, prop_text_by_prov, f1_by_prov],
        axis = 1
        )
    metrics_by_prov.columns = [
        "Number of pdfs included",
        "Number of pdfs with sections text",
        "Proportion of pdfs with sections text",
        "Lenient F1 score for all sections included"
        ]

    trans_n_text_by_sect = pd.DataFrame(
        [n_text_by_sect[provider] for provider in all_providers],
        index = all_providers
        )
    trans_n_text_by_sect.columns = [
        'Number of pdfs with a {} section'.format(b)\
        for b in trans_n_text_by_sect.columns
        ]
    trans_prop_text_by_sect = pd.DataFrame(
        [prop_text_by_sect[provider] for provider in all_providers],
        index = all_providers
        )
    trans_prop_text_by_sect.columns = [
        'Proportion with a {} section'.format(b)\
        for b in trans_prop_text_by_sect.columns
        ]
    trans_f1_by_sect = pd.DataFrame(
        [f1_by_sect[provider] for provider in all_providers],
        index = all_providers
        )
    trans_f1_by_sect.columns = [
        'Lenient F1 score for the {} section'.format(b)\
        for b in trans_f1_by_sect.columns
        ]

    provider_metrics = pd.concat(
        [metrics_by_prov, trans_n_text_by_sect,
        trans_prop_text_by_sect, trans_f1_by_sect],
        axis = 1,
        sort=True
        )
    provider_metrics.index.name = 'Provider'
    provider_metrics.reset_index(inplace=True)

    n = len(set(files))
    n_text = len(
            set([f for (f,a) in zip(files, actual) if a])
            )
    all_provider_metrics = {
        'Provider': 'all',
        'Number of pdfs included': n,
        'Number of pdfs with sections text': n_text,
        'Proportion of pdfs with sections text': round(n_text/n, 3),
        'Lenient F1 score for all sections included': round(
            f1_score(
                list(combined_data["Actual"]),
                list(combined_data["Predicted"]),
                average='micro'
            ), 3)
        }

    sections_texts = pd.DataFrame(
        {'Section': sections, 'Actual': actual, 'Predicted': predicted}
        )

    for section_name in set(sections):
        section_text = sections_texts[sections_texts['Section']==section_name]
        actual_section = section_text['Actual']
        predicted_section = section_text['Predicted']
        all_provider_metrics[
            'Number of pdfs with a {} section'.format(section_name)
            ] = len(set(
                [file for i,file in enumerate(files) if
                ((sections[i] == section_name) and (actual[i]))]
                ))
        all_provider_metrics[
            'Lenient F1 score for the {} section'.format(section_name)
            ] = f1_score(actual_section, predicted_section, average='micro')

    provider_metrics = provider_metrics.append(
        all_provider_metrics,
        ignore_index=True
        )
    provider_metrics = (provider_metrics.set_index('Provider').T)

    metrics = {
        'Lenient F1-score (references section exists or not)' : similarity,
        'Metrics by provider' : provider_metrics,
        }

    return metrics


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

    metrics = {
        'Number of pdfs with sections text' : len(scrape_data),
        'Mean normalised Levenshtein distance' : np.mean(lev_distances),
        'Strict accuracy (micro)' : np.mean(equal),
        'Lenient accuracy (micro) (normalised Levenshtein < {})'.format(
            levenshtein_threshold
            ) : np.mean(quite_equal)}

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

        metrics[
            'Mean normalised Levenshtein distance for the {} section'.format(
                section_name
                )
            ] = np.mean(lev_distances_section)
        metrics[
            'Strict accuracy for the {} section'.format(section_name)
            ] = strict_acc_section
        metrics[
            'Lenient accuracy (normalised Levenshtein'+
            '< {}) for the {} section'.format(
                levenshtein_threshold, section_name
                )
            ] = lenient_acc_section
    
    return {k:round(v,3) for k,v in metrics.items()}

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
    if os.path.splitext(pdf_name)[1] == ".pdf":
        pdf_name = os.path.splitext(pdf_name)[0]

    with open('{}/{}.pdf'.format(scrape_pdf_location, pdf_name), 'r') as f:
        pdf_file, full_text, _ = parse_pdf_document(f)
        scrape_data = []
        for section_name in section_names:
            scrape_data.append({
                'File' : pdf_name,
                'Section' : section_name,
                'Predicted text' : grab_section(pdf_file, section_name),
                'Actual text' : actual_texts[section_name]})
    return scrape_data


def evaluate_find_section(
        evaluate_find_section_data, provider_names,
        scrape_pdf_location, levenshtein_threshold
        ):

    # Get the predicted text for each of the pdf sections for each pdf
    section_names = evaluate_find_section_data[
        next(iter(evaluate_find_section_data))
        ].keys()
    scrape_data = []
    for pdf_name, actual_texts in evaluate_find_section_data.items():
        scrape_data.extend(
            scrape_process_pdf(
                section_names, pdf_name, scrape_pdf_location, actual_texts
                )
            )

    eval1_scores = evaluate_metric_scraped(
        [pred_section['Actual text']!='' for pred_section in scrape_data],
        [pred_section['Predicted text']!='' for pred_section in scrape_data],
        [pred_section['Section'] for pred_section in scrape_data],
        [pred_section['File'] for pred_section in scrape_data],
        [provider_names[pred_section['File']] for pred_section in scrape_data]
        )

    eval2_scores = evaluate_metric_quality(
        scrape_data,
        levenshtein_threshold)

    eval_scores_find = {
        "Score" : 1 - eval2_scores['Mean normalised Levenshtein distance']
        }
    eval_scores_find.update(eval1_scores)
    eval_scores_find.update(eval2_scores)

    return eval_scores_find

