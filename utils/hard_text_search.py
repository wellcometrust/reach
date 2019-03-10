import pandas as pd
import re

def clean_series_text(series):
	"""
	Input:
	-A pandas Series containing strings
	Output:
	-A pandas Series, with white space normalised and
	 non-alphanumeric characters removed
	Cleans up the text in a series such that it can easily be searched
	"""

	series = series.str.replace(
			"\\n", " "
		).str.replace(
			"\s{1,}", " "
		).str.replace(
			"[^A-Za-z0-9 ]", ""
		).str.lower()

	return (series)


def hard_text_search(scraped_text, clean_ref_file, fuzzy_matches):
	"""
	Input:
	-Raw scraped text, string
	-Cleaned references file, pandas DF
	-Fuzzy matches, pandas DF
	Output:
	-Extension to fuzzy_matches, with hard text search results concatenated
	"""

	fuzzy_matches['Tool'] = 'Policy'

	clean_scraped_text = clean_series_text(
		pd.Series(scraped_text.section)
	).to_frame()

	for _, clean_ref in clean_ref_file.iterrows():

		title = clean_ref['title']
		id = clean_ref['uber_id']

		#If there are new matches, append all relevant columns to the matched_refs DataFrame
		if not fuzzy_matches['WT_Ref_Id'].str.contains(id).any():
			if title in clean_scraped_text.iloc[0,0]:	

				refs_matched_with_title = pd.Series({
					'Document id'       : scraped_text.id,
					'Reference id'      : hash(title),
					'Title'             : title,
					'WT_Ref_Title'      : title,
					'WT_Ref_Id'         : id,
					'Cosine Similarity' : 1,
					'Tool'              : "Hard Text"
				}, index = [0])

				fuzzy_matches = fuzzy_matches.loc[:,~fuzzy_matches.columns.duplicated()]
				fuzzy_matches = fuzzy_matches.append(refs_matched_with_title, ignore_index=True)

	return (fuzzy_matches)