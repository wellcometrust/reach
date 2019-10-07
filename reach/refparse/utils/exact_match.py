import re


class ExactMatcher:
	def __init__(self, sectioned_documents, title_length_threshold):
		self.texts = [
			(doc.id, self.clean_text(doc.section))
			for doc in sectioned_documents
		]
		self.title_length_threshold = title_length_threshold

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

	def match(self, publication):
		"""
		Input:
			publication: dict that contains title and uber_id of academic publication
		Output:
			matched_reference: dict that links an academic publication with a policy document
		"""
		publication_title = self.clean_text(publication['title'])
		if len(publication_title) < self.title_length_threshold:
			return

		for doc_id, text in self.texts:

			if publication_title in text:
				yield {
					'Document id': doc_id,
					'Matched title': publication_title,
					'Matched publication id': publication['uber_id'],
					'Match algorithm': 'Exact match'
				}

		return
