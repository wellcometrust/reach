# policytool

Ultimately, all code will go in this directory, and this README will be superseded
by the toplevel README.

Meanwhile, this includes data on all code in this directory, including:

- airflow
- the scrapers run within airflow
- the policy tool API
- the policy tool website

![genericSpider](https://user-images.githubusercontent.com/235073/38735019-72dbd1f6-3f1f-11e8-9cb4-fa6f3d270dda.png)

A web scraper tool to get data for evaluating Wellcome impact.

## What do we scrape


 | Organisation | What is scraped                                                                     | Years       |
 |--------------|-------------------------------------------------------------------------------------|-------------|
 | WHO          | Everything on apps.who.int/iris                                                     | 2012 - 2019 |
 | NICE         | All the Guidances and evidences                                                     | 2000 - 2019 |
 | MSF          | All the reports and activity reports                                                | 2007 - 2019 |
 | GOV          | Everything from gov.uk/government/publications                                      | 1945 - 2019 |
 | UNICEF       | Everything from data.unicef.org/resources/resource-type/[publications and guidance] | 2010 - 2019 |
 | Parliament   | Everything from search-material.parliament.uk                                       | 1984 - 2019 |


## Development

To bring up the development environment using docker:

1. Start a clean postgres DB:
   ```
   docker-compose up -d
   ```
2. Build the base image
   ```
   make base_image
   ```

Then, to run a scraper from your local repo, run:

```
./docker_run.sh ./entrypoint.sh SPIDER_TO_RUN
```

where `SPIDER_TO_RUN` is one of:
  * `who_iris`
  * `gov_uk`
  * `nice`
  * `unicef`
  * `msf`
  * `parliament`

If you need to run outside docker, Dockerfile.base and entrypoint.sh
should point you in the right direction.

## Testing

To run tests, first bring up the development environment as above.

Then, run:

```
./docker_run.sh python -m unittest discover -s /pwd/tests
```

## Usage

To deploy this scraper yourself, see the wiki:
https://github.com/wellcometrust/wsf-web-scraper/wiki

This scraper can also be deployed more easily using Docker.

## Output Formatting

The outputed file is meant to contain a number a different fields, which
can vary depending on the scraper provider.

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

### Parliament

|Attribute|Description|
|---------|-----------|
|year     | the publication year of the document|
|types    | the type of the document |
