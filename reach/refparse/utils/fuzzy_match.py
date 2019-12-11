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
            publications(list): List of dicts containing publication info as
                above.
            similarity_threshold(float): Minimum allowable similarity
                threshold. If not results are found to have a similarity
                higher than this, then nothing is returned.
            title_length_threhold(int): Minimum allowed length of title.
                Less than this threshold will return no results.
        """
        # Filter out any publications that don't have titles assuming that the
        # input is a jsonl.

        publications = [i for i in publications if i.get("title")]

        # Create a list of the titles of the publications for creating the
        # tfidf matrix

        titles = [i["title"] for i in publications]

        # Index the remaining publications for faster searching

        self.publications = {i:pub for i, pub in enumerate(publications)}
        self.vectorizer = TfidfVectorizer(lowercase=True, ngram_range=(1, 1))
        self.tfidf_matrix = self.vectorizer.fit_transform(titles)
        self.similarity_threshold = similarity_threshold
        self.title_length_threshold = title_length_threshold

    def search_publications(self, reference, nb_results=10):
        """
        Args:
            reference(dict): A structured reference in a dict, that minimally
                contains the key: 'Title', but preferably 'Document id', and
                'Reference id'.
            nb_results(int): Number of results to return. This will be the top
                n results, ordered by similarity score.
        """
        title_vector = self.vectorizer.transform([reference.get("Title")])[0]
        title_similarities = cosine_similarity(title_vector, self.tfidf_matrix)[0]

        # Create a dict of similarities indexed by the order of the publications

        similarity_vector = {i:vector for i, vector in enumerate(title_similarities)}

        # Order the similarity vector by similarities (and subset the top nb_results)

        sorted_similarities = sorted(similarity_vector.items(), key=lambda item: item[1], reverse=True)
        sorted_similarities = sorted_similarities[0:nb_results]
        similar_doc_indices = [k for k, v in sorted_similarities]

        # Cycle through just the similar docs, not the entire list of
        # publications.

        retrieved_publications = {i:self.publications[i] for i in similar_doc_indices}

        # Finally append the similarity to the similar docs based on its index

        for key, doc in retrieved_publications.items():
            doc.update({"similarity": similarity_vector[key]})

        # Convert to a list, again checking that sorting is correct

        retrieved_publications = [value for key, value in retrieved_publications.items()]


        retrieved_publications = sorted(retrieved_publications, key=lambda x: x['similarity'], reverse=True)

        return retrieved_publications

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

        best_match = retrieved_publications[0]
        best_similarity = best_match.get("similarity")

        if best_similarity > self.similarity_threshold:
            return {
                "Document id": reference.get("Document id"),
                "Reference id": reference.get("Reference id"),
                "Extracted title": reference.get("Title"),
                "Matched title": best_match.get("title"),
                "Matched publication id": best_match.get("uber_id"),
                "Matched publication pmcid": best_match.get("pmcid"),
                "Matched publication pmid": best_match.get("pmid"),
                "Matched publication doi": best_match.get("doi"),
                "Similarity": best_similarity,
                "Match algorithm": "Fuzzy match",
            }

