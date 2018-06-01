#!/bin/bash

set -o nounset
set -o errexit

echo "Running $SPIDER_TO_RUN spider."
scrapy crawl "$SPIDER_TO_RUN"

exit 0
