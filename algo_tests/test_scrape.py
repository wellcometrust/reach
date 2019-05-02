
def test_metric_scraped(actual, predicted):
    """
    False positive rate
    """
    metric = 50 # Place holder

    return metric


def test_metric_quality(actual, predicted):
    """
    Text similarity
    """
    metric = 50 # Place holder

    return metric

def scrape_urls(scrape_test_data):

    references_text = []

    for url in scrape_test_data['url']:
        # data = scrape_function(url) #### NO IDEA HERE - SCRAPE THE URL GIVEN

        data = {'References section' : 'This was the references text.'} # Place holder
        
        if data['References section']:
            references_text.append(data['References section']) #### NO IDEA HERE - GET THE REFERENCES SECTION TEXT SCRAPED
        else:
            references_text.append(None) # It might be that nothing is scraped

    scrape_test_data['References section text scraped'] = references_text

    return scrape_test_data

def test_scrape(scrape_test_data):

    test1_2_info = scrape_urls(scrape_test_data)

    test1_score = test_metric_scraped(test1_2_info['Has a references section?'], test1_2_info['References section text scraped'])

    test2_score = test_metric_quality(test1_2_info['References section text'], test1_2_info['References section text scraped'])

    return test1_2_info, test1_score, test2_score


