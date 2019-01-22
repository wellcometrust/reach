# Wellcome Reference Parser
This repository uses a home trained model to identify components from a set of
scraped reference sections and to find those directly related to Wellcome.

## Requirements
This project use Pipenv to manage its dependencies.
It also requires a PostgreSQL server to store the results on production.

### Development
To develop for this project, you will need:
1. Python 3.5 or higher and `virtualenv`
2. PostgreSQL 9 or higher
3. A clean json file containing reference sections
4. A clean csv file containing all your references

Once you have everything installed, run:
  * `make virtualenv`
  * `source build/virtualenv/bin/activate`

## How to use it
### Method 1.
Use the manage.py command cli:

```
python manage.py [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  recreate_db  # Creates a parser_references database on your PostgreSQL server
  run_predict  # Runs the actual prediction
```
Running `run_predict` needs two arguments:
```
python manage.py run_predict [OPTIONS] SCRAPER_FILE REFERENCES_FILE
```
 Where SCRAPER_FILE is a Json file obtained through the web scraper and REFERENCES_FILE a CSV file containing the references.


### Method 2.
This repository includes a `settings.py` file, where you can manually configure your options.

Once you're happy with your configuration, just run `python main.py`

### Method 3.

Edit the `main.py` arguments in `run_parser.sh` to include the names of the input and output file locations desired. If the `scraper_file`, `references_file`, `model_file`, and `vectorizer_file` arguments are to S3 locations then make sure these start with `s3://`, otherwise file names are assumed to be locally stored. If the `output_url` argument is to a local location, then make sure it begins with `file://`, otherwise it is assumed to be from a database.

Then run in the terminal `./run_parser.sh`. 

## Contributing
See the [Contributing guidelines](./CONTRIBUTING.md)
