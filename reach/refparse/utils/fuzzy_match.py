import logging

import numpy as np

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


class FuzzyMatcher:
    def __init__(
        self, publications, similarity_threshold=0.8, title_length_threshold=0
    ):
        """
        Takes information about publications in the format:

        ```

        [
            {
            "pmid": 18568110,
            "pmcid": "PMC2424117",
            "title": "Fluvoxamine in the treatment of anxiety disorders.",
            "authors": [{"LastName": "Irons", "Initials": "J"}],
            "journalTitle": "Neuropsychiatric disease and treatment",
            "issue": "4",
            "journalVolume": "1",
            "pubYear": 2005,
            "journalISSN": "1176-6328",
            "pubType": "\"Journal Article\""
            },
            ...
        ]
        ```

        Args:
            publications(list): List of dicst containing publication info as
                above.
            similarity_threshold(float): Minimum allowable similarity
                threshold. If not results are found to have a similarity
                higher than this, then nothing is returned.
            title_length_threhold(float): Minimum allowed length of title.
                Less than this threshold will return no results.
        """
        # Filter out any publications that don't have titles

        publications = [pub for pub in publications if pub.get("title")]
        self.publications = pd.DataFrame(publications)
        self.vectorizer = TfidfVectorizer(lowercase=True, ngram_range=(1, 1))
        self.tfidf_matrix = self.vectorizer.fit_transform(self.publications.get("title"))
        self.similarity_threshold = similarity_threshold
        self.title_length_threshold = title_length_threshold

    def search_publications(self, reference, nb_results=10):
        """
        Args:
            reference(dict): A structure reference in a dict, that minimally
                contains the key: 'Title'.
            nb_results(int): Number of results to return. This will be the top
                n results, ordered by similarity score.
        """
        title_vector = self.vectorizer.transform([reference.get("Title")])[0]
        title_similarities = cosine_similarity(title_vector, self.tfidf_matrix)[0]
        retrieved_publications = self.publications.copy()
        retrieved_publications["similarity"] = title_similarities
        retrieved_publications.sort_values(
            by="similarity", ascending=False, inplace=True
        )

        return retrieved_publications[:nb_results]

    def match(self, reference):

        """
        Args:
            reference(dict): A structure reference in a dict, that minimally
                contains the key: 'Title'.
        """
        if not reference:
            return None

        if len(reference.get("Title")) < self.title_length_threshold:
            return None

        retrieved_publications = self.search_publications(reference)

        best_match = retrieved_publications.iloc[0]
        best_similarity = best_match.get("similarity")

        if best_similarity > self.similarity_threshold:
            return {
                "Document id": reference.get("Document id"),
                "Reference id": reference.get("Reference id"),
                "Extracted title": reference.get("Title"),
                "Matched title": best_match.get("title"),
                "Matched publication id": best_match.get("uber_id"),
                "Similarity": best_similarity,
                "Match algorithm": "Fuzzy match",
            }
