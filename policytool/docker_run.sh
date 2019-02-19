#!/bin/sh

docker run -ti --network wsfwebscraper_default \
    -v $(pwd):/pwd -w /pwd \
    web-scraper.base \
    $*
