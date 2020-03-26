.DEFAULT_GOAL := all

# ORG input default to the shortest one to run
ORG ?= msf

EPMC_DST := s3://datalabs-staging/etc etc je sais plus moi
SCRAPER_DST := s3://datalabs-dev/scraper/split-container/${ORG}/
PARSER_DST := s3://datalabs-dev/parser/split-container/${ORG}/policy_docs_normalized.json.gz

# This is only available on Mac at the time, linux users need to change it to localhost
DOCKER_LOCALHOST := host.docker.internal

# _____________
# TODO:
# When we're done with testing the splitter, we should run docker tasks demonized.
# _____________

.PHONY: base-image
base-image:
	docker build \
		-t reach.base \
		-f base/Dockerfile \
		./base

.PHONY: scraper-image
scraper-image: base-image
	docker build \
		-t uk.ac.wellcome/reach/scraper \
		-f scraper/Dockerfile \
		./scraper

.PHONY: parser-image
parser-image: base-image
	docker build \
		-t uk.ac.wellcome/reach/parser \
		-f parser/Dockerfile \
		./parser

.PHONY: extracter-image
extracter-image: base-image
	docker build \
		-t uk.ac.wellcome/reach/extracter \
		-f extracter/Dockerfile \
		./extracter

.PHONY: indexer-image
indexer-image: base-image
	docker build \
		-t uk.ac.wellcome/reach/indexer \
		-f es_indexer/Dockerfile \
		./es_indexer

.PHONY: docker-build
docker-build: base-image scraper-image parser-image


.PHONY: run-scraper
run-scraper: docker-build
	docker run \
	    -e AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID}" \
		-e AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY}" \
		-e SENTRY_DSN="${SENTRY_DSN}" \
	    uk.ac.wellcome/reach/scraper \
		${SCRAPER_DST} \
		${ORG}


.PHONY: run-parser
run-parser: docker-build
	docker run \
	    -e AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID}" \
		-e AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY}" \
		-e SENTRY_DSN="${SENTRY_DSN}" \
	    uk.ac.wellcome/reach/parser \
		${SCRAPER_DST} \
		${PARSER_DST} \
		${ORG}


.PHONY: run-extracter
run-extracter: extracter-image
	docker run \
	    -e AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID}" \
		-e AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY}" \
		-e SENTRY_DSN="${SENTRY_DSN}" \
	    uk.ac.wellcome/reach/extracter \
		${PARSER_DST} \
		s3://datalabs-dev/extracter/split-container/msf/extracted-refs-${ORG}.json.gz \
		s3://datalabs-dev/extracter-split/split-container/msf/split-refs-${ORG}.json.gz \

.PHONY: run-indexer-fulltexts
run-indexer-fulltexts: indexer-image
	docker run \
	    -e AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID}" \
		-e AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY}" \
		-e SENTRY_DSN="${SENTRY_DSN}" \
		-e ES_HOST=${DOCKER_LOCALHOST} \
		--network=host \
		uk.ac.wellcome/reach/indexer \
		${PARSER_DST} \
		${ORG} \
		fulltexts


.PHONY: docker-run
docker-run: docker-build run-scraper run-parser

.PHONY: all
all: docker-build
