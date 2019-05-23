import pandas as pd
import re

from ..settings import settings

class HardTextSearch:
	def __init__(self, ref_file):
		#Cleans up the ref file, changing from pandas DF to dict to reduce run time
		ref_file['clean_title'] = ref_file['title'].apply(lambda x: self.clean_text(x))
		ref_file = ref_file.loc[ref_file['clean_title'].str.len() >= settings.HARD_TEXT_MIN_CHAR_LIMIT]
		ref_file = ref_file.drop_duplicates()
		ref_file = ref_file.to_dict(orient = 'list')

		self.ref_file = ref_file


	def clean_text(self, string):
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

		return string


	def hard_text_search(self, scraped_text):
		"""
		Input:
		-Raw scraped text (named tuple, SectionedDocument)
		-IDs of matches already found by fuzzy matcher (pandas Series)
		Output:
		-Extension to matches, with hard text search results concatenated
		"""

		clean_scraped_text = self.clean_text(scraped_text.section)

		matches = pd.DataFrame()

		for i, title in enumerate(self.ref_file['clean_title']):

			#If there are new matches, append all relevant columns to the matched_refs DataFrame
			if title in clean_scraped_text:

				refs_matched_with_title = {
					'Document id'       : scraped_text.id,
					'Reference id'      : hash("UBER_ID:" + str( self.ref_file['uber_id'][i] )),
					'Title'             : title,
					'WT_Ref_Title'      : self.ref_file['title'][i],
					'WT_Ref_Id'         : self.ref_file['uber_id'][i],
					'Match_algorithm'   : "Text Search"
				}

				matches = matches.append(refs_matched_with_title, ignore_index=True)

		return matches
