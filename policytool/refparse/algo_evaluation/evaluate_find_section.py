
def evaluate_metric_scraped(actual, predicted):
    """
    False positive rate
    """
    # Place holder
    test_scores = {'Score' : 50, 'More info' : "More information about this test"}

    return test_scores


def evaluate_metric_quality(actual, predicted):
    """
    Text similarity
    """
    test_scores = {'Score' : 50, 'More info' : "More information about this test"}

    return test_scores

def scrape_pdfs(scrape_test_data):

    references_text = []

    for pdf in scrape_test_data['pdf']:
        # data = scrape_function(pdf) #### NO IDEA HERE - SCRAPE THE PDF (file location to pdf/text of pdf) GIVEN

        data = {'References section' : 'This was the references text.'} # Place holder
        
        if data['References section']:
            references_text.append(data['References section']) #### NO IDEA HERE - GET THE REFERENCES SECTION TEXT SCRAPED
        else:
            references_text.append(None) # It might be that nothing is scraped

    scrape_test_data['References section text scraped'] = references_text

    return scrape_test_data

def evaluate_find_section(scrape_test_data):

    test1_2_info = scrape_pdfs(scrape_test_data)

    test1_scores = evaluate_metric_scraped(test1_2_info['Has a references section?'], test1_2_info['References section text scraped'])

    test2_scores = evaluate_metric_quality(test1_2_info['References section text'], test1_2_info['References section text scraped'])

    return test1_scores, test2_scores


