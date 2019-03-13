import pandas as pd
import re


def clean_text(string):
	"""
	Input:
	-A string
	Output:
	-A string, with white space normalised and
	 non-alphanumeric characters removed
	Cleans up text such that it can easily be searched
	"""

	string = re.sub("\\n", " ", string)
	string = re.sub("\s{1,}", " ", string)
	string = re.sub("[^A-Za-z0-9 ]", "", string)

	string = string.lower()

	return (string)


def hard_text_search(scraped_text, ref_file, matches):
	"""
	Input:
	-Raw scraped text (named tuple, SectionedDocument)
	-Cleaned references file (dict, converted from pandas DF)
	-Matches found by the fuzzy matcher (pandas DF)
	Output:
	-Extension to matches, with hard text search results concatenated
	"""

	#Adds a flag, showing which process found the match, and removes duplicates
	matches['Tool'] = "Policy"
	matches = matches.loc[:,~matches.columns.duplicated()]

	clean_scraped_text = clean_text(scraped_text.section)

	for i in range(len(ref_file['title'])):

		title = ref_file['title'][i]
		uber_id = ref_file['uber_id'][i]

		#If there are new matches, append all relevant columns to the matched_refs DataFrame
		if not matches['WT_Ref_Id'].str.contains(uber_id).any():
			if title in clean_scraped_text:

				refs_matched_with_title = {
					'Document id'       : scraped_text.id,
					'Reference id'      : hash(title),
					'Title'             : title,
					'WT_Ref_Title'      : title,
					'WT_Ref_Id'         : uber_id,
					'Cosine_Similarity' : 1,
					'Tool'              : "Hard Text"
				}

				matches = matches.append(refs_matched_with_title, ignore_index=True)

	return (matches)