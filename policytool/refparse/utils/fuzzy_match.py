import numpy as np
import logging

import pandas as pd
from policytool.refparse.settings import settings
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


logger = logging.getLogger(__name__)

class FuzzyMatcher:
    def __init__(self, publications, similarity_threshold, title_length_threshold=0):
        self.publications = pd.DataFrame(publications)
        self.vectorizer = TfidfVectorizer(lowercase=True, ngram_range=(1, 1))
        self.tfidf_matrix = self.vectorizer.fit_transform(
            self.publications['title']
        )
        self.similarity_threshold = similarity_threshold
        self.title_length_threshold = title_length_threshold

    def search_publications(self, reference, nb_results=10):
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
        if not reference:
            return
        if len(reference['Title']) < self.title_length_threshold:
            return

        retrieved_publications = self.search_publications(reference)

        best_match = retrieved_publications.iloc[0]
        best_similarity = best_match['similarity']
        if best_similarity > self.similarity_threshold:
            return {
                'Document id': reference['Document id'],
                'Reference id': reference['Reference id'],
                'Extracted title': reference['Title'],
                'Matched title': best_match['title'],
                'Matched publication id': best_match['uber_id'],
                'Similarity': best_similarity,
                'Match algorithm': 'Fuzzy match'
            }
