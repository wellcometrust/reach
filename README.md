# MLReferenceSorter
Newest version Python script to structure unstructured references sections into Authors, Title, Journal, Year etc.

## Reference components model.ipynb
This is the workbook in which the model is trained. Data from a download of all 2017 Wellcome Trust acknowledged papers from Dimensions is used to predict what the different components of a reference look like - authors, title, jounral, publication year, volume, issue, pagination.

The model is flawed in it's classification of publication year since it was trained on data from 2017 only.

Steps in this workbook are:

#### 1. Import training set data and get it into a usable format
#### 2. Count the numbers of each word in every sentence
#### 3. Fit a Multinomial Naive Bayes classifier to the data
#### 4. Save the model

This workbook saves both the multinomial naive bayes classifier ('RefSorter_classifier.pkl') and the list of the words and their count in the training set ('RefSorter_vectorizer.pkl').


## Reference components predicting.ipynb

This workbook reads in the model from 'Reference components model.ipynb' and uses it to predict structured references from unstructured references.

The unstructured references are those scraped from the WHO website by Sam.

Steps in this workbook are:

#### 1. Load the model
#### 2. Predict unstructured data
#### 3. Group the same components in a reference

This is still being worked on.

## Reference components Fuzzy Matching

The fuzzy matching between titles found from the WHO documents and those known to be Wellcome Trust funded (from the Dimensions or EPMC data) was previous done in Alteryx. It'd be good to do it in python, although it takes a long time.

To save time (to have less data to match to) we can probably filter down the data it is compared to:

- can we filter by year? If the publication is from a year, then only compare to other pubs of this year?
- do we even care about all years?
- lots of the data points can't be matched anyway (since certain types of publications aren't in EPMC or Dimensions), so no point including them - e.g. all the WHO document references.



## Output of model

These files contain the predictions made by the model and are outputted in 'Reference components predicting.ipynb'.
