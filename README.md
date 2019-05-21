# Wellcome Policy Tool

Policy Tool is an open source service for discovering how research
publications are being cited in global policy documents, including those
produced by policy organizations such as the WHO, MSF, and the UK
government. Key parts of it include:

1. Web scrapers for pulling PDF documents from policy organizations,
1. A reference parser for extracting references from these documents,
1. A task for sourcing publications from EuropePMC,
1. A task for matching references to publications, and
1. An Airflow installation for automating web scraping, reference
   parsing, publication sourcing, and reference matching.

Work on a REST API and minimal search interface are forthcoming in early
Q2 2019.

Policy Tool is written in Python and developed using docker-compose. Key
dependencies are:

- a Kubernetes cluster that supports persistent volumes
- a PostgreSQL or MySQL database for Airflow to use
- a distributed storage service such as S3
- (soon) an ElasticSearch cluster for searching documents

Although parts of the Policy Tool have been in use at Wellcome since
mid-2018, the project has only just gone open source starting in March
2019. Given these early days, please be patient as various parts of it
are made accessible to external users. All issues and pull requests
are welcome. Contributing guidelines can be found in
[CONTRIBUTING.md](./CONTRIBUTING.md).

### Dependencies
To develop for this project, you will need:
1. Python 3.5 or higher and `virtualenv`
1. Docker and docker-compose
1. AWS credentials
1. A clean json file containing reference sections
1. A clean csv file containing all your references

Once you have everything installed, run:
  * `make virtualenv`
  * `source build/virtualenv/bin/activate`

### Starting docker-compose given you have Wellcome creds

```
eval $(./export_env.py)
docker-compose up -d
```

### Running a task

```

```


## airflow

See [wsf-web-scraper/README.md](wsf-web-scraper/README.md).

## Wellcome Reference Parser

The top-level files in this repo currently hold Policy Tool's reference
parser, which uses a home trained model to identify components from a
set of scraped reference sections and to find those directly related to
Wellcome.

## How to use it

Make an output folder `output_folder_name` and run `refparse.py` with arguments of your file locations, e.g. for msf in the terminal run:

```
mkdir -p ./tmp/parser-output/output_folder_name

python ./refparse.py \
    --scraper-file "s3://datalabs-data/scraper-results/msf/20190117.json" \
    --references-file "file://./references_folder/references_file.csv" \
    --model-file "s3://datalabs-data/reference_parser_models/reference_parser_pipeline.pkl" \
    --output-url "file://./tmp/parser-output/output_folder_name"
```

If the `scraper_file`, `references_file`, `model_file`, arguments are to S3 locations then make sure these start with `s3://`, otherwise file names are assumed to be locally stored. If the `output_url` argument is to a local location, then make sure it begins with `file://`, otherwise it is assumed to be from a database.

### Merging results
The parsed and matched references from each documents are saved in a separate file in the output folder. You can merge all of them together by running
```
python merge_results.py \
    --references-file "file://./references_folder/references_file.csv" \
    --output-url  "./tmp/parser-output/output_folder_name"
```

### Wellcome only

If you would like to run the parser for the latest scraped files and to save the output locally, then run the following:
```
python parse_latest.py msf \
    --references-file "s3://datalabs-data/wellcome_publications/uber_api_publications.csv" \
    --output-url "file://./tmp/parser-output"
```

If you want to specify the arguments for the other inputs then you can, otherwise default values will be given:

```
python ./parse_latest.py msf \
    --references-file "s3://datalabs-data/wellcome_publications/uber_api_publications.csv" \
    --model-file "s3://datalabs-data/reference_parser_models/reference_parser_pipeline.pkl" \
    --output-url "file://./tmp/parser-output/output_folder_name"
```

Warning that this could take some time.

## Unit testing
You can run the unittests for this project by running:
`make docker-test`

This will test that your last changes didn't affect how the program works.

## Evaluating each component of the algorithm

We have devised some evaluation data in order to evaluate 5 steps of the model. The results can be found by first downloading the evaluation data from [here](https://s3-eu-west-1.amazonaws.com/datalabs-data/policy_tool_tests), and then running
```
python evaluate_algo.py --verbose True
```
(set the verbose argument to False if you want less information about the evaluation to be printed).

## Contributing
See the [Contributing guidelines](./CONTRIBUTING.md)
