In this document we describe how we got each of the evaluation datasets uses in `test_algo.py`.

## Scrape Evaluation

"./algo_evaluation/data_evaluate/scrape_test_data.csv"

## Split Section Evaluation

"./algo_evaluation/data_evaluate/split_section_test_data.csv"
"./algo_evaluation/data_evaluate/scraped_references_sections/* "

## Parse Evaluation

"./algo_evaluation/data_evaluate/actual_reference_structures_sample.csv"

Up to 10 references from 39 policy documents (13 WHO, 10 UNICEF, 6 MSF and 10 NICE policy documents) were chosen randomly. The text of the reference was copied and pasted from the pdf, and then we decided which parts of the reference were from each of the categories (setting to blank if there wasn't a particular category for this reference).

## Match Evaluation

"./algo_evaluation/data_evaluate/positive_and_negative_match_test_data.csv"
"./algo_evaluation/data_evaluate/uber_api_publications.csv"

We randomly selected 200 references from a list of Wellcome Trust publications from Uber Dimensions ("uber_api_publications.csv"). With this list (the 'positive' list) we used the fuzzy match algorithm to find a list (the 'negative' list) of the second most similar references to them (i.e. the best match would be the reference in question, and the second would be quite similar). The positive list was reduced to 199 since one reference didn't have a second strong match, and the negative list gave 202 references since for some references there were multiple references with the same cosine similarity competing for second place. In the match evaluation we match both the positive and negative lists against a copy of "uber_api_publications.csv" but with the negative list of references removed. Thus, if our matching is working perfectly the references in the positive list should all be matched and the references in the negative list should not be matched.


