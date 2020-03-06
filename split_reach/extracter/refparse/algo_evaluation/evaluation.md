In this document we describe how we got each of the evaluation datasets uses in `evaluate_algo.py`. This data can be downloaded [here](https://s3-eu-west-1.amazonaws.com/datalabs-data/policy_tool_tests) and are stored in the repository [here](reach/refparse/algo_evaluation/data_evaluate). We also describe the output when running `evaluate_algo`.


## Find Evaluation
### Data
- We generated a random list of policy documents from each provider currently scraped (using the Postico publication database).
- We went through this list until we found at least 5 which had a section that contain references and 5 that didn't.
- We ignored documents which had multiple references sections.
- The pdfs for these were saved in "./algo_evaluation/data_evaluate/pdfs", named with a unique identifier for this pdf.
- We looked for the text from sections Reach currently looks for in the pdfs ('reference' and 'bibliograph'), stored [here](reach/resources/section_keywords.txt).
- The text was copied and pasted from the pdf (starting from the section name to the last character of the section) into a text editor and saved as a .txt file in the relevant sections folder (e.g. "./algo_evaluation/data_evaluate/pdf_sections/reference") and saved with the same unique name as the pdf was.


### Evaluation Scores
- We use the functions `parse_pdf_document` and `grab_section` from `reach/pdf_parser/pdf_parse.py` to predict the references sections from each of the pdfs in our evaluation.

Using this data we return two types of information. One shows how well we identify if there is a references section or not, and one to see how well we get the actual text of this section.
1. Whether a pdf has or doesn't have a references section is compared to whether our functions predict there to be a references section or not, returning a F1 score. We also return a classification report and a confusion matrix for this comparison, and also give these scores broken down by each references section type (e.g. 'reference' and 'bibliograph').
2. In the pdfs which do have a references section, we find the normalised Levenshtein distances for each of the actual and predicted references section texts. The proportion of pdfs with exactly the same actual and predicted texts is returned - the 'Strict accuracy', and we also return a more lenient score of the proportion where texts are closely similar (this is defined by a threshold parameter - `LEVENSHTEIN_DIST_SCRAPER_THRESHOLD`) - the 'Lenient accuracy'.

Our overall evaluation score is one minus the mean normalised Levenshtein distance, and hence the closer this score is to one the more similar our predicted section text is to the actual section text, and closer to zero the least similar it is.

## Split Evaluation
### Data
- Randomly sample policy documents with scraped references sections.
- Made a decision about the quality of the scrape - if it was bad then we wouldn't include, but if the references text scraped included the whole references text we took it forward. We have 6 documents from MSF documents, 20 from NICE, 10 from UNICEF, and 17 from WHO documents.
- Make a decision about where the references started and ended. There was often a lot of non-references text scraped after the references.
- Copy and paste the references section only into a txt file (with the document hash as the file name) stored in the "scraped_references_sections" folder.
- Manually count the number of references from this document's pdf, record in "split_section_test_data.csv".

### Evaluation Scores
- We use the function `split_section` from `reach/refparse/utils/split.py` to predict how many references there are from each of the references section texts.
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

### Evaluation Score
- Using the model found in `MODEL_FILE_PREFIX` given by the parameter `MODEL_FILE_NAME` we use the `structure_reference` function from `reach/refparse/utils/parse.pdf` to predict all the reference categories for each of the evaluation references texts.
- We calculate the Levenshtein distances for each reference category, and find the proportion of these categories which are predicted exactly (thus if there are 7 reference catgories for 205 references then we have (7x205) 1435 data points to compare) - the 'Strict accuracy'.
- We also return the proportion which are quite similarly predicted (using the parameter `LEVENSHTEIN_DIST_PARSE_THRESHOLD`) - the 'Lenient accuracy', and break down the results by category.
- Our overall evaluation score is one minus the mean normalised Levenshtein distance, and hence the closer this score is to one the more similar our predicted components are to the actual components, and closer to zero the least similar it is. 


## Match Evaluation

### Data
- We selected the first 100,000 references from a list of EPMC publications ("epmc-metadata.json").
- We randomly selected a sample 20,000 from these. The second 10,000 of these were removed from the full list of 100,000 references, leaving 90,000 references.
- The references in the first 10,000 from the sample were matched (using `FuzzyMatcher` from `reach/refparse/utils`) against the 90,000 references, and the seconf 10,000 from the sample were matched against the 90,000 references.
- Thus we have a list of 20,000 reference matches, 10,000 where they should match exactly to themselves (and thus the match id is their own reference id), and 10,000 where there should be no match found (match id is None).

### Evaluation Score
- We predict the matches for each of the 20,000 references returning a list of the reference ids that the references was found to match to (or None if no match was found).
- Our final evaluation score is the F1 score of these actual and predicted lists.
- We also record whether the match found was correct or not, which can be found by comparing the uber ids of the reference and it's match. Thus we also return a classification report and the frequency table of match types.

### Evaluation Thresholds

Summary: Filtering out 'matches' where the cosine similarity is less than 0.6 and the title length is less than 33 will remove lots of false positives. However, this comes at the expensive of filtering out some true positives. Thus, we made a decision (which can be challenged) that we would optimise for precision, which means that we want to be confident that our predicted matches are correct, whilst knowing that we won't have predicted all of the matches.

Considerations: Do we want to be confident that the matches are correct but we also have some false negatives? Or do we want to be confident that we haven’t got any false positives at the expense of missing some true positives?

For this evaluation we also considered the thresholds to use when predicting whether a match should be taken forward or not. For this we plotted all the cosine similarities found from the actual = "Negative" set (i.e. the second best matches). We also investigated the relationship between cosine similarity and title length.

<p float="left">
  <img src="exploratory/negative_cosines_hist_2019-07-01-1211.png" width="500" />
  <img src="exploratory/negative_cosines_len_scatter_2019-07-01-1211.png" width="250" />
</p>

From these we can see that generally the cosine similarity is quite low, but when it is high (>0.8) the title length tends to be quite short. Thus we saw that if we set the match and title length thresholds to be relatively high then we'd reduce the number of false positives. The 95th percentile of the cosine similarities is 0.6 and the 5th percentile of the title length is 33.

We also looked at the distribution of title lengths in the actual = "Positive" set (i.e. where they should match exactly, hence all the matches have a cosine similarity of 1). Since we can also have incorrect matches in this set - which is where a reference has the same title as another one, we plot both the correct and incorrectly matched references from the positive set. The 5th percentile of the title length is 35.

<p align="center">
  <img src="exploratory/title_lengths_2019-07-01-1211.png" width="500" />
</p>

From this we see that the incorrect matches occur when the title lengths are quite low. Thus, we can set the title length threshold to be high enough to remove some false negatives, but this is at the expense of removing some true positives.

We varied these two thresholds and recorded some metrics. In our algorithm it's important that if we say there is a match then we are confident it is a true match (high precision). We picked the default match threshold to be 0.8 and the length threshold to be 50 based on all of these plots.

<p float="left">
  <img src="exploratory/thresholds_F1Score_negative_heatmap_2019-07-01-1211.png" width="250" />
  <img src="exploratory/thresholds_Recall_negative_heatmap_2019-07-01-1211.png" width="250" />
  <img src="exploratory/thresholds_Precision_negative_heatmap_2019-07-01-1211.png" width="250" />
</p>
