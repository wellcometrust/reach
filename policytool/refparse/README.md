# Wellcome Reference Parser

Wellcome Reach's reference parser uses a home trained model to identify
components from a set of scraped reference sections.

## How to use it

Make an output folder `output_folder_name` and run `refparse.py` with
arguments of your file locations, e.g. for msf in the terminal run:

```
mkdir -p ./tmp/parser-output/output_folder_name

python ./refparse.py \
    --scraper-file "s3://datalabs-data/scraper-results/msf/20190117.json" \
    --references-file "file://./references_folder/references_file.csv" \
    --model-file "s3://datalabs-data/reference_parser_models/reference_parser_pipeline.pkl" \
    --output-url "file://./tmp/parser-output/output_folder_name"
```

If the `scraper_file`, `references_file`, `model_file`, arguments are to
S3 locations then make sure these start with `s3://`, otherwise file
names are assumed to be locally stored. If the `output_url` argument is
to a local location, then make sure it begins with `file://`, otherwise
it is assumed to be from a database.

### Merging results

The parsed and matched references from each documents are saved in a
separate file in the output folder. You can merge all of them together
by running

```
python merge_results.py \
    --references-file "file://./references_folder/references_file.csv" \
    --output-url  "./tmp/parser-output/output_folder_name"
```

### Wellcome only

If you would like to run the parser for the latest scraped files and to
save the output locally, then run the following:

```
python parse_latest.py msf \
    --references-file "s3://datalabs-data/wellcome_publications/uber_api_publications.csv" \
    --output-url "file://./tmp/parser-output"
```

If you want to specify the arguments for the other inputs then you can,
otherwise default values will be given:

```
python ./parse_latest.py msf \
    --references-file "s3://datalabs-data/wellcome_publications/uber_api_publications.csv" \
    --model-file "s3://datalabs-data/reference_parser_models/reference_parser_pipeline.pkl" \
    --output-url "file://./tmp/parser-output/output_folder_name"
```

Warning that this could take some time.

## Evaluating each component of the algorithm

We have devised some evaluation data in order to evaluate 5 steps of the model. The results can be calculated by first installing poppler
```
brew install poppler
```
and then downloading the evaluation data from [here](https://s3-eu-west-1.amazonaws.com/datalabs-data/policy_tool_tests) and storing it in `algo_evaluation/data_evaluate/`, which can be done in the command line by running
```
aws s3 cp --recursive s3://datalabs-data/policy_tool_tests algo_evaluation/data_evaluate/
```
and
```
aws s3 cp s3://datalabs-staging/airflow/output/open-research/epmc-metadata/epmc-metadata.json.gz .
download: s3://datalabs-staging/airflow/output/open-research/epmc-metadata/epmc-metadata.json.gz to algo_evaluation/data_evaluate/epmc-metadata.json.gz
gunzip epmc-metadata.json.gz
```
and finally running
```
python evaluate_algo.py --verbose True
```
(or set the verbose argument to False if you want less information about the evaluation to be printed).

You can read more about how we got the evaluation data and what the evaluation results mean [here](algo_evaluate/evaluation_data.md).
