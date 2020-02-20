.DEFAULT_GOAL := all

.PHONY: base-image
base-image:
	docker build \
		-t reach.base \
		-f base/Dockerfile \
		./base

.PHONY: scraper-image
scraper-image:
	docker build \
		-t uk.ac.wellcome/reach/scraper \
		-f scraper/Dockerfile \
		./scraper

.PHONY: docker-build
docker-build: base-image scraper-image


.PHONY: docker-run-scraper
docker-run: docker-build
	docker run -d \
	    -e ./base/dev.env \
	    uk.ac.wellcome/reach/scraper \
		s3://datalabs-dev/scraper/split-container/ \
		msf


.PHONY: all
all: docker-build
