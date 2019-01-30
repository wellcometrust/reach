import os
from settings import settings

gov_uk = os.environ['GOVUK_S3_URL']
msf = os.environ['MSF_S3_URL']
nice = os.environ['NICE_S3_URL']
parliament = os.environ['PARLIAMENT_S3_URL']
unicef = os.environ['UNICEF_S3_URL']
who_iris = os.environ['WHO_S3_URL']

latest_names = {
				'gov_uk': gov_uk, 
				'msf': msf,
				'nice': nice, 'parliament':parliament, 'unicef':unicef,'who_iris':who_iris
				}

# Use these to run the parser for the organisations with regex:
organisation_regex = list(settings._regex_dict.keys())

for organisation in organisation_regex:

	latest_name_organisation = latest_names[organisation]

	# The directory will just have the name of the organisation and the date of scrape
	folder_name = organisation + latest_name_organisation[-13:-5]
	dir_name = './tmp/parser-output/{}'.format(folder_name)

	if not os.path.exists(dir_name):
		os.mkdir(dir_name)

	run_script = 'python3 main.py \
	 	--scraper-file "s3://datalabs-data/{}" \
	 	--references-file "s3://datalabs-data/wellcome_publications/uber_api_publications.csv" \
	 	--model-file "s3://datalabs-data/reference_parser_models/RefSorter_classifier.pkl" \
	 	--vectorizer-file "s3://datalabs-data/reference_parser_models/RefSorter_vectorizer.pkl" \
	 	--output-url "file://{}"'.format(latest_name_organisation, dir_name)

	os.system(run_script)
