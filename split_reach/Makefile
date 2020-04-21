.DEFAULT_GOAL := all

# ORG input default to the shortest one to run
ORG ?= msf

EPMC_METADATA_KEY = s3://datalabs-staging/airflow/output/open-research/epmc-metadata/epmc-metadata.json.gz

SCRAPER_DST := s3://datalabs-dev/scraper/split-container/${ORG}/
PARSER_DST := s3://datalabs-dev/parser/split-container/${ORG}/policy_docs_normalized.json.gz

EXTRACTER_PARSED_DST := s3://datalabs-dev/extracter/split-container/${ORG}/extracted-refs-${ORG}.json.gz
EXTRACTER_SPLIT_DST := s3://datalabs-dev/extracter-split/split-container/${ORG}/split-refs-${ORG}.json.gz

FUZZYMATCHER_DST := s3://datalabs-dev/fuzzymatcher/split-container/${ORG}/fuzzymatched-refs-${ORG}.json.gz

# This is only available on Mac at the time, linux users need to change it to localhost
DOCKER_LOCALHOST := host.docker.internal

ECR_ARN := 160358319781.dkr.ecr.eu-west-1.amazonaws.com
VERSION := latest


# _____________
# TODO:
# When we're done with testing the splitter, we should run docker tasks demonized.
# Also all the pipeline related images are meant to be run in Argo, not just like that.
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
		-t ${ECR_ARN}/reach/scraper \
		-f scraper/Dockerfile \
		./scraper

.PHONY: parser-image
parser-image: base-image
	docker build \
		-t ${ECR_ARN}/reach/parser \
		-f parser/Dockerfile \
		./parser

.PHONY: extracter-image
extracter-image: base-image
	docker build \
		-t ${ECR_ARN}/reach/extracter \
		-f extracter/Dockerfile \
		./extracter

.PHONY: indexer-image
indexer-image: base-image
	docker build \
		-t ${ECR_ARN}/reach/indexer \
		-f es_indexer/Dockerfile \
		./es_indexer

.PHONY: fuzzymatcher-image
fuzzymatcher-image: base-image
	docker build \
		-t ${ECR_ARN}/reach/fuzzymatcher \
		-f fuzzymatcher/Dockerfile \
		./fuzzymatcher

.PHONY: docker-build
docker-build: base-image scraper-image parser-image extracter-image indexer-image fuzzymatcher-image


.PHONY: run-scraper
run-scraper: scraper-image
	docker run \
	    -e AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID}" \
		-e AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY}" \
		-e SENTRY_DSN="${SENTRY_DSN}" \
	    ${ECR_ARN}/reach/scraper \
		${SCRAPER_DST} \
		${ORG}


.PHONY: run-parser
run-parser: parser-image
	docker run \
	    -e AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID}" \
		-e AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY}" \
		-e SENTRY_DSN="${SENTRY_DSN}" \
	    ${ECR_ARN}/reach/parser \
		${SCRAPER_DST} \
		${PARSER_DST} \
		${ORG}


.PHONY: run-extracter
run-extracter: extracter-image
	docker run \
	    -e AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID}" \
		-e AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY}" \
		-e SENTRY_DSN="${SENTRY_DSN}" \
	    ${ECR_ARN}/reach/extracter \
		${PARSER_DST} \
		${EXTRACTER_PARSED_DST} \
		${EXTRACTER_SPLIT_DST}

.PHONY: run-indexer-fulltexts
run-indexer-fulltexts: indexer-image
	docker run \
	    -e AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID}" \
		-e AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY}" \
		-e SENTRY_DSN="${SENTRY_DSN}" \
		-e ES_HOST=${DOCKER_LOCALHOST} \
		--network=host \
		${ECR_ARN}/reach/indexer \
		${PARSER_DST} \
		${ORG} \
		fulltexts

.PHONY: run-indexer-epmc
run-indexer-epmc: indexer-image
	docker run \
	    -e AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID}" \
		-e AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY}" \
		-e SENTRY_DSN="${SENTRY_DSN}" \
		-e ES_HOST=${DOCKER_LOCALHOST} \
		--network=host \
		${ECR_ARN}/reach/indexer \
		${EPMC_METADATA_KEY} \
		${ORG} \
		epmc \
		--max_items=10000

.PHONY: run-fuzzymatcher
run-fuzzymatcher: fuzzymatcher-image
	docker run \
	    -e AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID}" \
		-e AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY}" \
		-e SENTRY_DSN="${SENTRY_DSN}" \
		-e ES_HOST=${DOCKER_LOCALHOST} \
		--network=host \
		${ECR_ARN}/reach/fuzzymatcher \
		${EXTRACTER_PARSED_DST} \
		${FUZZYMATCHER_DST} \
		${ORG} \
		fulltexts


.PHONY: run-indexer-citations
run-indexer-citations: indexer-image
	docker run \
	    -e AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID}" \
		-e AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY}" \
		-e SENTRY_DSN="${SENTRY_DSN}" \
		-e ES_HOST=${DOCKER_LOCALHOST} \
		--network=host \
		${ECR_ARN}/reach/indexer \
		${FUZZYMATCHER_DST} \
		${ORG} \
		citations


.PHONY: docker-run
docker-run: docker-build run-scraper run-parser run-extracter run-indexer-epmc run-indexer-citations



# Testing
.PHONY: tests-image
tests-image: base-image
	docker build \
		-t ${ECR_ARN}/reach/testing \
		-f Dockerfile.tests \
		.

.PHONY: docker-test
docker-test: tests-image
	docker run -u root -v $$(pwd)/requirements.tests.txt:/requirements.tests.txt \
		--rm $(ECR_IMAGE):$(VERSION) \
		sh -c "pip3 install -r /requirements.tests.txt && pytest /opt/reach"



# Web application
.PHONY: web-image
web-image:
	docker build \
	    -t ${ECR_ARN}/reach/web \
		-f web/Dockerfile \
		web

.PHONY: all
all: docker-build
