#!/bin/bash

set -o errexit

if [[ -z "$SCRAPY_YEARS" ]]; then
  YEARS_LIST=''
else
  YEARS_LIST="-a years_list=\"$SCRAPY_YEARS\""
fi
if [[ -z "$SCRAPY_OPTIONS" ]]; then
    OPTIONS_LIST=''
else
    OPTIONS_LIST=$SCRAPY_OPTIONS
fi
if [[ -z "$SPIDER_TO_RUN" ]]; then
    echo "Either you did not specify a spider, or the spider you want to run does not exist."
    exit 1
fi

echo "Running scrapy crawl $SPIDER_TO_RUN $YEARS_LIST $OPTIONS_LIST"
scrapy crawl "$SPIDER_TO_RUN" $YEARS_LIST $OPTIONS_LIST

exit 0
