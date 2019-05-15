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


