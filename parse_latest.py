"""
This code lets you run the reference parser with the latest scraped documents from several organisations.
You can input as an argument the name of the references you want to match the parsed references against.
e.g. 
python parse_latest.py "file://./wellcome_publications/uber_api_publications.csv"
or just 
python parse_latest.py
which will match against the uber wellcome publications stored in S3 
"""

from argparse import ArgumentParser
from urllib.parse import urlparse
import os
import sys
import boto3

from settings import settings
from refparse import parse_references


parser = ArgumentParser(description=__doc__.strip())

ORG_NAMES = (
    'gov_uk',
    'msf',
    'nice',
    'parliament',
    'unicef',
    'who_iris'
)
parser.add_argument('org_name', choices=ORG_NAMES)

# gov_uk = os.environ.get('GOVUK_S3_URL', None)
# msf = os.environ.get('MSF_S3_URL', None)
# nice = os.environ.get('NICE_S3_URL', None)
# parliament = os.environ.get('PARLIAMENT_S3_URL', None)
# unicef = os.environ.get('UNICEF_S3_URL', None)
# who_iris = os.environ.get('WHO_S3_URL', None)




"""
    Argument is the references file you want to match the parsed references against
    If local this should start with 'file://'
    try:
        references_file = sys.argv[1]
    except:
        references_file = "s3://datalabs-data/wellcome_publications/uber_api_publications.csv"

    # Use these to run the parser for the organisations with regex:
    organisation_regex = list(settings._regex_dict.keys())

    for organisation in organisation_regex:

        latest_name_organisation = latest_names[organisation]
        print(latest_name_organisation)
        # If there was an environmental variable for this organisation
        if latest_name_organisation:
            # The directory name will be the name of the organisation 
            # and the date of scrape (which is the name of the file)
            folder_name = organisation + os.path.basename(latest_name_organisation)
            dir_name = './tmp/parser-output/{}'.format(folder_name)

            if not os.path.exists(dir_name):
                os.mkdir(dir_name)

            run_script = 'python3 main.py \
                 --scraper-file "s3://datalabs-data/{}" \
                 --references-file {} \
                 --model-file "s3://datalabs-data/reference_parser_models/RefSorter_classifier.pkl" \
                 --vectorizer-file "s3://datalabs-data/reference_parser_models/RefSorter_vectorizer.pkl" \
                 --output-url "file://{}"'.format(latest_name_organisation, references_file, dir_name)

            os.system(run_script)

"""

if __name__ == "__main__":
    args = parser.parse_args()
    org = args.org_name

    s3prefix = os.path.join(settings.SCRAPER_RESULTS_BASEDIR, org)
    u = urlparse(s3prefix)
    bucket_name, prefix = u.netloc, u.path[1:]

    s3 = boto3.resource('s3')

    my_bucket = s3.Bucket(bucket_name)

    # Get the most recently scraped filename
    key_name, obj = max(
        (obj.key, obj) for obj in my_bucket.objects.filter(Prefix=prefix).all()
    )

    # The directory name will be the name of the organisation 
    # and the date of scrape (which is the name of the file)
    folder_name = org + os.path.splitext(os.path.basename(key_name))[0]
    dir_name = './tmp/parser-output/{}'.format(folder_name)

    if not os.path.exists(dir_name):
        os.mkdir(dir_name)

    run_script = 'python3 refparse.py \
         --scraper-file "s3://datalabs-data/{}" \
         --references-file "s3://datalabs-data/wellcome_publications/uber_api_publications.csv" \
         --model-file "s3://datalabs-data/reference_parser_models/RefSorter_classifier.pkl" \
         --vectorizer-file "s3://datalabs-data/reference_parser_models/RefSorter_vectorizer.pkl" \
         --output-url "file://{}"'.format(org, dir_name)

    os.system(run_script)

