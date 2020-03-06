.DEFAULT_GOAL := all

SCRAPER_DST := s3://datalabs-dev/scraper/split-container/msf/

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

.PHONY: parser-image
parser-image:
	docker build \
		-t uk.ac.wellcome/reach/parser \
		-f parser/Dockerfile \
		./parser

.PHONY: extracter-image
extracter-image:
	docker build \
		-t uk.ac.wellcome/reach/extracter \
		-f extracter/Dockerfile \
		./extracter

.PHONY: docker-build
docker-build: base-image scraper-image parser-image


.PHONY: docker-run-scraper
docker-run-scraper: docker-build
	docker run \
	    -e AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID}" \
		-e AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY}" \
		-e SENTRY_DSN="${SENTRY_DSN}" \
	    uk.ac.wellcome/reach/scraper \
		${SCRAPER_DST} \
		msf


.PHONY: docker-run-parser
docker-run-parser: docker-build
	docker run \
	    -e AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID}" \
		-e AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY}" \
		-e SENTRY_DSN="${SENTRY_DSN}" \
	    uk.ac.wellcome/reach/parser \
		${SCRAPER_DST} \
		s3://datalabs-dev/parser/split-container/msf/ \
		msf

.PHONY: all
all: docker-build
