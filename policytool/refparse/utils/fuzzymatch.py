import numpy as np
import pandas as pd
from policytool.refparse.settings import settings
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

        if isinstance(predicted_publications, pd.Series):
            predicted_publications = predicted_publications.to_frame().transpose()

        if predicted_publications.shape[0] == 0:
            return pd.DataFrame({
                'Document id': [],
                'Reference id': [],
                'Title': [],
                'title': [],
                'uber_id': [],
                'Cosine_Similarity': [],
                'Match_algorithm': "Fuzzy Matcher"
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

        # Get indices of highest cosine similarity over threshold for each predicted publication row
        # In form [(0, 77523), (1, 5258), (2, 66691) ..., (398, 94142)]]
        max_above_threshold_indices_pairs = np.array([
                # If there are multiple indices of the maximum value for this row then pick one randomly
                (i, np.random.choice(np.argwhere(row==np.max(row)).flatten())) 
                for i,row in enumerate(title_similarities)\
                if np.max(row)>self.threshold
               ])
        # Edge case where there are no matches over the threshold:
        if max_above_threshold_indices_pairs.shape[0] == 0:
            predicted_indices = np.array([])
            real_indices = np.array([])
            cosine_similarities = np.array([])
        else:
            predicted_indices = max_above_threshold_indices_pairs[:,0]
            real_indices = max_above_threshold_indices_pairs[:,1]
            cosine_similarities = title_similarities[
                (predicted_indices, real_indices)
            ]

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

        match_data['Match_algorithm'] = "Fuzzy Matcher"

        return match_data

    def fuzzy_match(self, predicted_publications):

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

        if not all_match_data.empty:
            self.logger.info(all_match_data.head())
        return all_match_data
