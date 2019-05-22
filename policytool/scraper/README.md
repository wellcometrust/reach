# scraper

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
