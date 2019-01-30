"""
This code lets you run the reference parser with the latest scraped documents from several organisations.
You can input as an argument the name of the references you want to match the parsed references against.
e.g. 
python parse_latest.py "file://./wellcome_publications/uber_api_publications.csv"
or just 
python parse_latest.py
which will match against the uber wellcome publications stored in S3 
"""

import os
import sys
from settings import settings

gov_uk = os.environ.get('GOVUK_S3_URL', None)
msf = os.environ.get('MSF_S3_URL', None)
nice = os.environ.get('NICE_S3_URL', None)
parliament = os.environ.get('PARLIAMENT_S3_URL', None)
unicef = os.environ.get('UNICEF_S3_URL', None)
who_iris = os.environ.get('WHO_S3_URL', None)

latest_names = {
'gov_uk': gov_uk,
'msf': msf,
'nice': nice,
'parliament':parliament,
'unicef':unicef,
'who_iris':who_iris
}

if __name__ == "__main__":
	"""
	Argument is the references file you want to match the parsed references against
	If local this should start with 'file://'
	"""
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

