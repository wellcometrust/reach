"""
This code is used to merge the matched results together after running the parser
Manually edit main with the folder names you want to merge all together
Output is one csv of all the matches from all the organisations you have provided
"""

from argparse import ArgumentParser
import fnmatch
import os
import glob

import pandas as pd

from .refparse import get_file


def get_csv_names(output_url, suffix):
    """
    This function goes to a folder location and returns a list
    of all the names of the csvs within it.
    Input: 
        output_url - the file directory to look in
        suffix - the suffix of the csv name
    Output: 
        csv_names - a list of csv folder/filenames
    """
    csv_names = glob.glob(
        os.path.join(output_url, '**/*{}.csv'.format(suffix)), recursive=True
    )

    return csv_names

def concat_match_csvs(match_csv_names):
    """
    This function merges all the csvs given in match_csv_names
    Input:
        match_csv_names -  a list of _all_match_data.csv folder/filenames
    Output:
        all_matches - a dataframe containing all the merged match csvs
    """
    all_matches = []
    for match_csv_name in match_csv_names:
        try:
            match_data = pd.read_csv(match_csv_name)
        except:
            print(match_csv_name)
            continue
        if not match_data.empty:
            all_matches.append(match_data)

    if not all_matches:
        return pd.DataFrame({
            'Document id': [],
            'WT_Ref_Id': []
        })

    return pd.concat(all_matches)

def concat_predicted_csvs(predicted_csv_names):
    """
    This function gets all the document id & document url from the predicted references csv
    Input:
        predicted_csv_names -  a list of _predicted_reference_structures.csv folder/filenames
    Output:
        all_url - a dataframe containing document id and document url
    """
    all_predicted_references = []
    all_url = []
    for predicted_csv_name in predicted_csv_names:
        # Some (4) of the files don't read in without errors
        try:
            pred_data = pd.read_csv(predicted_csv_name)
        except:
            print('Read csv issue for file {}'.format(predicted_csv_name))
        if not pred_data.empty:
            all_predicted_references.append(pred_data)
            # Each row has the same doc id and doc url, so only need to use first row
            all_url.append({'Document id' : pred_data.iloc[0]['Document id'],
                'Document uri' : pred_data.iloc[0]['Document uri']})

    all_url = pd.DataFrame.from_dict(all_url)
    all_predicted_references = pd.concat(all_predicted_references)
    return all_url, all_predicted_references

def create_argparser(description):
    parser = ArgumentParser(description)
    parser.add_argument(
        '--output-url',
        help='Directory of saved output folders'
    )
    parser.add_argument(
        '--references-file',
        help='Original references file which was used in parsing of saved outputs'
    )
    return parser

if __name__ == '__main__':

    parser = create_argparser(__doc__.strip())
    args = parser.parse_args()

    output_url = args.output_url
    output_folder_name = 'merged_all_matches'

    ref_file = get_file(args.references_file, 'csv')

    match_csv_names = get_csv_names(output_url, '_all_match_data')
    predicted_csv_names = get_csv_names(output_url, '_predicted_reference_structures')

    all_match = concat_match_csvs(match_csv_names)
    all_url, all_predicted_references = concat_predicted_csvs(predicted_csv_names)

    all_matches_url = all_match.join(
        all_url.set_index('Document id'),
        on='Document id'
        ) # Join with url
    
    all_matches_refs = all_matches_url.join(
        ref_file.set_index('uber_id'),
        on='WT_Ref_Id'
        ) # Join with references information

    if not os.path.exists('{}/{}'.format(output_url, output_folder_name)):
            os.makedirs('{}/{}'.format(output_url, output_folder_name))

    all_matches_refs.to_csv('{}/{}/merged_all_matches.csv'.format(output_url, output_folder_name))
    all_predicted_references.to_csv('{}/{}/merged_all_predicted_reference_structures.csv'.format(output_url, output_folder_name))
