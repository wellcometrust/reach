In this document we describe how we got each of the evaluation datasets uses in `evaluate_algo.py`. This data can be downloaded [here](https://s3-eu-west-1.amazonaws.com/datalabs-data/policy_tool_tests) and are stored in the repository [here](policytool/refparse/algo_evaluation/data_evaluate). We also describe the output when running `evaluate_algo`.


## Find Sections Evaluation
### Data
- We generated a random list of policy documents we currently scrape from various policy organisations.
- We went through this list until we found X which had a section that contain references and X that didn't.
- The pdfs for these were saved in "./algo_evaluation/data_evaluate/pdfs", named with a unique identifier for this pdf.
- We looked for the text from sections Reach currently looks for in the pdfs ('reference' and 'bibliograph'), stored [here](policytool/resources/section_keywords.txt).
- The text was copied and pasted from the pdf into a markdown file and saved as a .txt file in the relevant sections folder (e.g. "./algo_evaluation/data_evaluate/pdf_sections/reference") and saved with the same unique name as the pdf was.


### Evaluation Scores 1 and 2
- We use the functions `parse_pdf_document` and `grab_section` from `policytool/pdf_parser/pdf_parse.py` to predict the references sections from each of the pdfs in our evaluation.

Using this data we return two scores, one to see how well we identify if there is a references section or not, and one to see how well we get the actual text of this section.
1. Whether a pdf has or doesn't have a references section is compared to whether our functions predict there to be a references section or not, returning a F1 score. We also return a classification report and a confusion matrix for this comparison, and also give these scores broken down by each references section type (e.g. 'reference' and 'bibliograph').
2. In the pdfs which do have a references section, we find the normalised Levenshtein distances for each of the actual and predicted references section texts. The proportion of pdfs with exactly the same actual and predicted texts is returned - the 'Strict accuracy', and we also return a more lenient score of the proportion where texts are closely similar (this is defined by a threshold parameter - `LEVENSHTEIN_DIST_SCRAPER_THRESHOLD`) - the 'Lenient accuracy'.

## Split Section Evaluation
### Data
- Randomly sample policy documents with scraped references sections.
- Made a decision about the quality of the scrape - if it was bad then we wouldn't include, but if the references text scraped included the whole references text we took it forward. We have 6 documents from MSF documents, 20 from NICE, 10 from UNICEF, and 17 from WHO documents.
- Make a decision about where the references started and ended. There was often a lot of non-references text scraped after the references.
- Copy and paste the references section only into a txt file (with the document hash as the file name) stored in the "scraped_references_sections" folder.
- Manually count the number of references from this document's pdf, record in "split_section_test_data.csv".


### Evaluation Score 3
- We use the function `split_section` from `policytool/refparse/utils/split.py` to predict how many references there are from each of the references section texts.
- We can see how well the section was split by looking at how similar the numbers of references are, using the difference metric:
```
abs(100*((predicted number - actual number) / actual number))
```
- Our evaluation score is the percentage of evaluation points which have this metric less than a threshold (`SPLIT_SECTION_SIMILARITY_THRESHOLD`).
- We also return the median difference metric, and break down these scores by each policy organisation.

## Parse Evaluation

### Data
- Up to 10 references from 39 policy documents (13 WHO, 10 UNICEF, 6 MSF and 10 NICE policy documents) were chosen randomly, resulting in 205 references.
- The text of the reference was copied and pasted from the pdf, and then we decided which parts of the reference were from each of the categories (setting to blank if there wasn't a particular category for this reference).
- This data is stored in "actual_reference_structures_sample.csv"

### Evaluation Score 4
- Using the model found in `MODEL_FILE_PREFIX` given by the parameter `MODEL_FILE_NAME` we use the `structure_reference` function from `policytool/refparse/utils/parse.pdf` to predict all the reference categories for each of the evaluation references texts.
- We calculate the Levenshtein distances for each reference category, and find the proportion of these categories which are predicted exactly (thus if there are 7 reference catgories for 205 references then we have (7x205) 1435 data points to compare) - the 'Strict accuracy'.
- We also return the proportion which are quite similarly predicted (using the parameter `LEVENSHTEIN_DIST_PARSE_THRESHOLD`) - the 'Lenient accuracy', and break down the results by category.


## Match Evaluation

### Data
- We randomly selected 200 references from a list of Wellcome Trust publications from Uber Dimensions ("uber_api_publications.csv").
- With this list (the 'positive' list) we used the fuzzy match algorithm to find a list (the 'negative' list) of the second most similar references to them (i.e. the best match would be the reference in question, and the second would be quite similar).
- The positive list was reduced to 199 since one reference didn't have a second strong match, and the negative list gave 202 references since for some references there were multiple references with the same cosine similarity competing for second place.
- We take the titles and publication IDs from these and combine them in "positive_and_negative_match_test_data.csv" where we record a 1 or 0 for the positive and negative lists respectively in 'Do we expect a match?'.

### Evaluation Score 5
- We remove the references with 'Do we expect a match?' = 0 from "uber_api_publications.csv", this is our 'publication set'.
- We use `FuzzyMatcher` from `policytool/refparse/utils` to predict whether the reference titles in the evaluation data are matched with any of those from the publication set.
- We compare 'Do we expect a match?' with whether we found a true match or not, returning the F1 score.
- We also return a classification report and the frequency table of match types (the reference was matched to the same reference in the publication set (True), the reference was matched to a different reference in the publication set (False), or there was no match found).


