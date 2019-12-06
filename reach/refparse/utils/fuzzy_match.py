import numpy as np
import logging

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


logger = logging.getLogger(__name__)

class FuzzyMatcher:
    def __init__(self, publications, similarity_threshold=0.8, title_length_threshold=0):
        """
        Args:
            publications(list): A list of dicts containing reference information
                from a canonical list of publications, which minially contain
                the key 'title'.
            similarity_threshold(float): Minimum allowable similarity
                threshold. If not results are found to have a similarity
                higher than this, then nothing is returned.
            title_length_threhold(float): Minimum allowed length of title.
                Less than this threshold will return no results.
        """
        self.publications = pd.DataFrame(publications)
        self.vectorizer = TfidfVectorizer(lowercase=True, ngram_range=(1, 1))
        self.tfidf_matrix = self.vectorizer.fit_transform(
            self.publications['title']
        )
        self.similarity_threshold = similarity_threshold
        self.title_length_threshold = title_length_threshold

    def search_publications(self, reference, nb_results=10):
        """
        Args:
            reference(dict): A structure reference in a dict, that minimally
                contain the key: 'title'.
            nb_results(int): Number of results to return. This will be the top
                n results, ordered by similarity score.
        """
        title_vector = self.vectorizer.transform(
            [reference['Title']]
        )[0]
        title_similarities = cosine_similarity(
            title_vector, self.tfidf_matrix
        )[0]
        retrieved_publications = self.publications.copy()
        retrieved_publications['similarity'] = title_similarities
        retrieved_publications.sort_values(by='similarity', ascending=False, inplace=True)
        return retrieved_publications[:nb_results]

    def match(self, reference):
        """
        Args:
            reference(dict): A structure reference in a dict, that minimally
                contain the key: 'Title'.
        """

        if not reference:
            return None
        if len(reference['Title']) < self.title_length_threshold:
            return None

        retrieved_publications = self.search_publications(reference)

        best_match = retrieved_publications.iloc[0]
        best_similarity = best_match['similarity']
        if best_similarity > self.similarity_threshold:
            return {
                'Matched title': best_match['title'],
                'Matched publication id': best_match['uber_id'],
                'Similarity': best_similarity,
                'Match algorithm': 'Fuzzy match'
            }

