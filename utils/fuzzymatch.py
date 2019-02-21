import numpy as np
import pandas as pd
from settings import settings
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class FuzzyMatcher:
    def __init__(self, real_publications, match_threshold):
        self.logger = settings.logger
        self.vectorizer = TfidfVectorizer(lowercase=True, ngram_range=(1, 1))
        self.tfidf_matrix = self.vectorizer.fit_transform(
            real_publications['title']
        )
        self.real_publications = real_publications
        self.threshold = match_threshold

    def match_vectorised(self, predicted_publications):

        if predicted_publications.shape[0] == 0:
            return pd.DataFrame({
                'Document id': [],
                'Reference id': [],
                'Title': [],
                'title': [],
                'uber_id': [],
                'Cosine_Similarity': []
            })

        # Todo - Make sure not resetting index works the same
        predicted_publications.dropna(
            subset=['Title'],
            inplace=True
        )
        title_vectors = self.vectorizer.transform(
            predicted_publications['Title']
        )

        title_similarities = cosine_similarity(
            title_vectors, self.tfidf_matrix
        )
        above_threshold_indices = np.nonzero(
            title_similarities > self.threshold
        )
        cosine_similarities = title_similarities[
            above_threshold_indices
        ]

        predicted_indices, real_indices = above_threshold_indices
        
        match_data = pd.concat([
            predicted_publications.iloc[predicted_indices][[
                'Document id',
                'Reference id',
                'Title']].reset_index(),
            self.real_publications.iloc[real_indices][[
                'title',
                'uber_id']].reset_index(),
            pd.DataFrame({
                'Cosine_Similarity': cosine_similarities
            }).reset_index()],
            axis=1)

        return match_data

    def fuzzy_match(self, predicted_publications):
        self.logger.info(
            "Fuzzy matching for %s predicted publications ...",
            len(predicted_publications)
        )

        all_match_data = self.match_vectorised(
            predicted_publications
        )
        all_match_data.rename(
            columns={
                'title': 'WT_Ref_Title',
                'uber_id': 'WT_Ref_Id'
            },
            inplace=True
        )

        self.logger.info(all_match_data.head())
        return all_match_data
