import numpy as np
import pandas as pd
from settings import settings
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class FuzzyMatcher:
    def __init__(self, real_publications, titles):
        self.logger = settings.logger
        self.vectorizer = TfidfVectorizer(lowercase=True, ngram_range=(1, 1))
        self.tfidf_matrix = self.vectorizer.fit_transform(
            real_publications['title']
        )
        self.real_publications = real_publications

    def match_vectorised(self, predicted_publications, threshold):
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

        high_similarity_indices = np.argwhere(
            title_similarities > threshold
        )
        
        predicted_index = high_similarity_indices[:,0]
        real_index = high_similarity_indices[:,1]
        
        match_data = pd.concat([
            predicted_publications.iloc[predicted_index][[
                'Document id',
                'Reference id',
                'Title']],
            self.real_publications.iloc[real_index][[
                'title',
                'uber_id']],
            pd.DataFrame({
                'Cosine_Similarity': [title_similarities[t[0]][t[1]] for t in high_similarity_indices]
            })],
            axis=1)
        
        return match_data

    def fuzzy_match(self, predicted_publications, threshold):
        self.logger.info(
            "Fuzzy matching for %s predicted publications ...",
            len(predicted_publications)
        )

        all_match_data = pd.DataFrame(
            self.match_vectorised(
                predicted_publications,
                threshold
            ),
            columns=[
                'Document id',
                'Reference id',
                'Predicted_Ref_Title',
                'WT_Ref_Title',
                'WT_Ref_Id',
                'Cosine_Similarity'
            ]
        )

        self.logger.info(all_match_data.head())
        return all_match_data
