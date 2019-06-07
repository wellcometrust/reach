# Wellcome Reference Parser

Wellcome Reach's reference parser uses home trained models to identify
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
    --splitter-model-file "s3://datalabs-data/reference_splitter_models/line_iobe_pipeline_20190502.dll" \
    --output-url "file://./tmp/parser-output/output_folder_name"
```

If the `scraper_file`, `references_file`, `model_file` and `splitter_model_file`, arguments are to
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
    --splitter-model-file "s3://datalabs-data/reference_splitter_models/line_iobe_pipeline_20190502.dll" \
    --output-url "file://./tmp/parser-output/output_folder_name"
```

Warning that this could take some time.

