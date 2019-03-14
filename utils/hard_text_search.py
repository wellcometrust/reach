import pandas as pd
import re

class HardTextSearch:
	def __init__(self, ref_file, min_chars):
		#Cleans up the ref file, changing from pandas DF to dict to reduce run time
		ref_file['title'] = [self.clean_text(x) for x in ref_file['title']]
		ref_file = ref_file.loc[ref_file['title'].str.len() >= min_chars]
		ref_file = ref_file.drop_duplicates(subset = 'title')
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

		return (string)


	def hard_text_search(self, scraped_text, refs_to_exclude):
		"""
		Input:
		-Raw scraped text (named tuple, SectionedDocument)
		-IDs of matches already found by fuzzy matcher (pandas Series)
		Output:
		-Extension to matches, with hard text search results concatenated
		"""

		#Removes refs already found by fuzzy matcher
		indices_to_exclude = [i for i,x in enumerate(self.ref_file['uber_id']) if x in refs_to_exclude]
		for i in sorted(indices_to_exclude, reverse = True):
			del self.ref_file['title'][i]
			del self.ref_file['uber_id'][i]

		clean_scraped_text = self.clean_text(scraped_text.section)

		matches = pd.DataFrame()

		for i in range(len(self.ref_file['title'])):

			title = self.ref_file['title'][i]
			uber_id = self.ref_file['uber_id'][i]

			#If there are new matches, append all relevant columns to the matched_refs DataFrame
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