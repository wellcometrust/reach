# wsf-web-scraper

![genericSpider](https://user-images.githubusercontent.com/235073/38735019-72dbd1f6-3f1f-11e8-9cb4-fa6f3d270dda.png)

A web scraper tool to get data for evaluating Wellcome impact.

## Installation

### Common steps
Install Postgresql (https://www.postgresql.org/) and create a `wsf_scraping` database
Clone this repository

Run the content of `scraper.sql` as a SQL query on your postresql database

## Unsing Docker
Install Docker (https://www.docker.com/get-started)
Run `docker build -t wsf-scraper .`
Create a `local.env` file containing the following environment variables:
```
DATABASE_URL=postgres://postgres:postgres@localhost:5432/wsf_scraping
DATABASE_URL_TEST=postgres://postgres:postgres@localhost:5432/wsf_scraping_test

S3_ACCESS_KEY=[Your AWS key]
S3_SECRET_KEY=[Your AWS secret]
S3_BUCKET=wsf_scraping_results

SPIDER_TO_RUN=[who_iris|gov_uk|nice|unicef|msf]

```
Run `docker run wsf-scraper --env-file=local.env`

### Without Docker
This project uses Pipenv. Instructions to install it can be found here: https://pipenv.readthedocs.io/en/latest/
Once you installed pipenv, just run `pipenv install` to setup you local repository.
To parse PDF, this repository needs Poppler: https://poppler.freedesktop.org/
If you're on any unix system, you can use your packet manager to install `poppler-utils` and `libpoppler-cpp-dev`.

Configure your options in `settings.py`
Export the following variables in your terminal:
```
DATABASE_URL=postgres://postgres:postgres@localhost:5432/wsf_scraping
DATABASE_URL_TEST=postgres://postgres:postgres@localhost:5432/wsf_scraping_test
```
You can run the scraper using `pipenv run scrapy crawl [spider_name]` or activating a pipenv shell using `pipenv shell` and then run `scrapy crawl [spider_name]`


## Usage

To deploy this scraper yourself, see the wiki: https://github.com/wellcometrust/wsf-web-scraper/wiki

This scraper can also be deployed more easily using Docker.

## Output Formatting

The outputed file is meant to contain a number a different fields, which can vary depending on the scraper provider.

It will always have the following attributes, though:

|Unique|Attribute|Description|
|------|---------|-----------|
|      |title    | a string containing the document title|
|*     |uri      | the url of the document|
|      |pdf      | the name of the file|
|      |sections | a json object of section names, containing the text extracted from matching sections|
|      |keywords | a json object of keywords, containing the text extracted from matching text|
|*     |hash     | a md5 digest of the file|
|      |provider | the provider from where the file has been downloaded|
|      |date_scraped | the date (YYYYMMDD) when the article has been scraped|

Some providers will have additional parameters:

### WHO

|Attribute|Description|
|---------|-----------|
|year     | the publication year of the document|
|types    | an array containing the WHO type associated with the document|
|subjects | an array containing the WHO subjects of the document|
|authors  | an array containing the authors (from WHO)|

### Nice

|Attribute|Description|
|---------|-----------|
|year     | the publication year of the document|
