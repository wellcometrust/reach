"""
This code is used to merge the matched results together after running the parser
Manually edit main with the folder names you want to merge all together
Output is one csv of all the matches from all the organisations you have provided
"""

import fnmatch
import os
import glob

import pandas as pd


def get_csv_names(file_dir, suffix):
    """
    This function goes to a folder location and returns a list
    of all the names of the csvs within it.
    Input: 
        file_dir - the file directory to look in
        suffix - the suffix of the csv name
    Output: 
        csv_names - a list of csv folder/filenames
    """
    csv_names = glob.glob(
        os.path.join(file_dir, '**/*{}.csv'.format(suffix)), recursive=True
    )

    return csv_names

def merge_match_csvs(match_csv_names):
    """
    This function merges all the csvs given in match_csv_names
    Input:
        match_csv_names -  a list of _all_match_data.csv folder/filenames
    Output:
        all_matches - a dataframe containing all the merged match csvs
    """
    all_matches = []
    for match_csv_name in match_csv_names:
        match_data = pd.read_csv(match_csv_name)
        if not match_data.empty:
            all_matches.append(match_data)

    all_matches = pd.concat(all_matches, ignore_index=False)

    return all_matches


def merge_predicted_csvs(predicted_csv_names):
    """
    This function gets all the document id & document url from the predicted references csv
    Input:
        predicted_csv_names -  a list of _predicted_reference_structures.csv folder/filenames
    Output:
        all_url - a dataframe containing document id and document url
    """
    all_url = []
    for predicted_csv_name in predicted_csv_names:
        # Some (4) of the files don't read in without errors
        try:
            pred_data = pd.read_csv(predicted_csv_name)
        except:
            print('Read csv issue for file {}'.format(predicted_csv_name))
        if not pred_data.empty:
            # Each row has the same doc id and doc url, so only need to use first row
            all_url.append({'Document id' : pred_data.iloc[0]['Document id'],
                'Document uri' : pred_data.iloc[0]['Document uri']})

    all_url = pd.DataFrame.from_dict(all_url)

    return all_url

if __name__ == '__main__':

    file_dir = './tmp/parser-output/charlene' # "pophealth", "charlene"
    output_name = 'merged_all_matches'
    
    match_refs = pd.read_csv(
        "./match-references/charlene_publications_format.csv")
    # "./match-references/MRC_Publications_Nov2018_JGHT_JHSRI_all.csv"
    # "./match-references/charlene_publications_format.csv"

    match_csv_names = get_csv_names(file_dir, '_all_match_data')
    predicted_csv_names = get_csv_names(file_dir, '_predicted_reference_structures')

    all_match = merge_match_csvs(match_csv_names)
    all_url = merge_predicted_csvs(predicted_csv_names)

    all_matches_url = all_match.join(
        all_url.set_index('Document id'),
        on='Document id'
        ) # Join with url
    
    all_matches_refs = all_matches_url.join(
        match_refs.set_index('uber_id'),
        on='WT_Ref_Id'
        ) # Join with references information

    if not os.path.exists('{}/{}'.format(file_dir, output_name)):
            os.makedirs('{}/{}'.format(file_dir, output_name))

    all_matches_refs.to_csv('{}/{}/merged_all_matches.csv'.format(file_dir, output_name))


