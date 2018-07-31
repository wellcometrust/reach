import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class FuzzyMatcher():

    def __init__(self, real_publications, titles):
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            ngram_range=(1, 1)
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(
            real_publications['title']
        )
        self.titles = real_publications['title']
        self.ids = real_publications['uber_id']

    def match_vectorised(self, predicted_publications, threshold):
        # Get rid of ones without titles and reset
        # index (important for next steps)
        predicted_publications = predicted_publications.loc[pd.notnull(
            predicted_publications['Title']
        )].reset_index()

        title_vectors = self.vectorizer.transform(
            predicted_publications['Title']
        )
        title_similarities = cosine_similarity(
            title_vectors, self.tfidf_matrix
        )

        # Save all the titles which match with over the threshold
        # similarity, if any
        high_similarity_index = tuple(np.argwhere(
            title_similarities > threshold)
        )

        # The predicted publication indexes of the similar matches
        predicted_index = [t[0] for t in high_similarity_index]

        # The real publication indexes of the similar matches
        real_index = [t[1] for t in high_similarity_index]

        match_data = np.column_stack(
            (predicted_publications['Document id'][predicted_index],
             predicted_publications['Reference id'][predicted_index],
             predicted_publications['Title'][predicted_index],
             self.titles[real_index],
             self.ids[real_index],
             [title_similarities[t[0]][t[1]] for t in high_similarity_index])
        )
        return match_data

    def fuzzy_match_blocks(self, blocksize, predicted_publications, threshold):
        print(
            "Fuzzy matching for " + str(
                len(predicted_publications)
            ) + " predicted publications ..."
        )

        counter = 0
        nextblocksize = blocksize

        all_match_data = []
        while counter < len(predicted_publications):
            match_data = self.match_vectorised(
                predicted_publications[counter:(counter + nextblocksize)],
                threshold
            )

            counter = counter + nextblocksize

            # How many to go through in the next block (default is blocksize
            # unless there aren't enough left)
            if (len(predicted_publications) - counter) >= blocksize:
                nextblocksize = blocksize
            else:
                # Just do the remainder next time
                nextblocksize = len(predicted_publications) - counter
            for m in match_data:
                all_match_data.append(m)

        all_match_data = pd.DataFrame(
            all_match_data,
            columns=['Document id', 'Reference id', 'Predicted_Ref_Title',
                     'WT_Ref_Title', 'WT_Ref_Id', 'Cosine_Similarity']
        )

        print(all_match_data.head())
        return all_match_data
