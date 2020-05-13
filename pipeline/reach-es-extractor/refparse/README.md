# Wellcome Reference Parser

Wellcome Reach's reference parser uses a home trained model to identify
components from a set of scraped reference sections.

## How to use it

Make an output folder and run `refparse` with arguments of your file
locations. E.g., from the main `reach` directory, you might make and
activate the virtualenv and then run it like so:

```
make virtualenv
. build/virtualenv/bin/activate
mkdir -p /tmp/refparse-out
python -m reach.refparse.refparse \
    --scraper-file "s3://datalabs-dev/reach-airflow/output/policy/parsed-pdfs/msf/parsed-pdfs-msf.json.gz" \
    --references-file "s3://datalabs-data/wellcome_publications/uber_api_publications.csv" \
    --model-file "s3://datalabs-data/reference_parser_models/reference_parser_pipeline.pkl" \
    --output-dir /tmp/refparse-out
```

If the `scraper_file`, `references_file`, `model_file`, arguments are to
S3 locations then make sure these start with `s3://`, otherwise file
names are assumed to be locally stored.

For a complete list of arguments, run:

```
python -m reach.refparse.refparse -h
```

### Merging results

The parsed and matched references from each documents are saved in a
separate file in the output folder. You can merge all of them together
by running

```
python -m reach.refparse.merge_results \
    --references-file "s3://datalabs-data/wellcome_publications/uber_api_publications.csv" \
    --output-url  "./tmp/parser-output/output_folder_name"
```

### Wellcome only

If you would like to run the parser for the latest scraped files and to
save the output locally, then run the following:

```
python -m reach.refparse.parse_latest msf \
    --references-file "s3://datalabs-data/wellcome_publications/uber_api_publications.csv" \
    --output-url "file://./tmp/parser-output"
```

If you want to specify the arguments for the other inputs then you can,
otherwise default values will be given:

```
python -m reach.refparse.parse_latest msf \
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
aws s3 cp s3://datalabs-staging/airflow/output/open-research/epmc-metadata/epmc-metadata.json.gz algo_evaluation/data_evaluate/epmc-metadata.json.gz
gunzip epmc-metadata.json.gz
```
and finally running
```
python evaluate_algo.py --verbose True
```
(or set the verbose argument to False if you want less information about the evaluation to be printed).

You can read more about how we got the evaluation data and what the evaluation results mean [here](https://github.com/wellcometrust/reach/blob/master/reach/refparse/algo_evaluation/evaluation.md).
