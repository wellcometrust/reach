"""
This code is used to merge the matched results together after running the parser
Manually edit main with the folder names you want to merge all together
Output is one csv of all the matches from all the organisations you have provided
"""

import os
import pandas as pd

def get_matches(all_matches, all_uri, file_dir):
    """
    Read all the match files from a file directory
    Append any matches found to all_matches
    If there is a match then append the uri to all_uri
    """
    for file in os.listdir(file_dir):
        if file.endswith("_all_match_data.csv"):
            match_data = pd.read_csv("{}/{}".format(file_dir,file))
            if not match_data.empty:
                all_matches.append(match_data)
                pred_data = pd.read_csv("{}/{}_predicted_reference_structures.csv".format(file_dir,file.split("_")[0]))
                all_uri.append(pred_data[['Document id','Document uri']].drop_duplicates())

    return all_matches, all_uri

def merge_matches(folder_name, org_list, match_refs):
    """
    Get all the _all_match_data.csv files for all organisations
    Concat them all and join to the original references data
    """
    all_matches = []
    all_uri = []
    for org in org_list:
        file_dir = "{}/{}".format(folder_name, org)
        all_matches, all_uri = get_matches(all_matches, all_uri, file_dir)

    all_matches = pd.concat(all_matches, ignore_index=False)
    all_uri = pd.concat(all_uri, ignore_index=False)
    
    all_matches_url = all_matches.join(
        all_uri.set_index('Document id'),
        on='Document id'
        ) # Join with url
    
    all_matches_refs = all_matches_url.join(
        match_refs.set_index('uber_id'),
        on='WT_Ref_Id'
        ) # Join with references information

    return all_matches_refs

if __name__ == '__main__':

    # The name you used in your output file name
    job_name = "charlene" # "pophealth"
    
    # The original references data searched for
    match_refs = pd.read_csv(
        "/Users/gallaghe/Code/reference-parser/match-references/charlene_publications_format.csv")
    # "/Users/gallaghe/Code/reference-parser/match-references/MRC_Publications_Nov2018_JGHT_JHSRI_all.csv"

    folder_name = "/Users/gallaghe/Code/reference-parser/tmp/parser-output"
    who_iris = "{}_who_iris20190207".format(job_name)
    unicef = "{}_unicef20190131".format(job_name)
    msf = "{}_msf20190131".format(job_name)
    nice = "{}_nice20190131".format(job_name)

    all_matches_refs = merge_matches(folder_name, [who_iris, unicef, msf, nice], match_refs)

    all_matches_refs.to_csv('{}/{}_all_matches.csv'.format(folder_name, job_name))
