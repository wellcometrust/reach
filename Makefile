.DEFAULT_GOAL := all

# ORG input default to the shortest one to run
ORG ?= msf

ifdef IMAGE_REPO_NAME
WEB_IMAGE := ${IMAGE_REPO_NAME}
else
WEB_IMAGE := uk.ac.wellcome/reach
endif

EPMC_METADATA_KEY = s3://datalabs-staging/airflow/output/open-research/epmc-metadata/epmc-metadata.json.gz

SCRAPER_DST := s3://datalabs-dev/scraper/split-container/${ORG}/
PARSER_DST := s3://datalabs-dev/parser/split-container/${ORG}/policy_docs_normalized.json.gz

EXTRACTER_PARSED_DST := s3://datalabs-dev/extracter/split-container/${ORG}/extracted-refs-${ORG}.json.gz
EXTRACTER_SPLIT_DST := s3://datalabs-dev/extracter-split/split-container/${ORG}/split-refs-${ORG}.json.gz

FUZZYMATCHER_DST := s3://datalabs-dev/fuzzymatcher/split-container/${ORG}/fuzzymatched-refs-${ORG}.json.gz

DEEP_REFERENCE_PARSER_WHEEL := deep_reference_parser-2020.4.5-py3-none-any.whl
DEEP_REFERENCE_PARSER_URL := https://github.com/wellcometrust/deep_reference_parser/releases/download/2020.4.29/$(DEEP_REFERENCE_PARSER_WHEEL)

# This is only available on Mac at the time, linux users need to change it to localhost
DOCKER_LOCALHOST := host.docker.internal

ECR_ARN := 160358319781.dkr.ecr.eu-west-1.amazonaws.com/uk.ac.wellcome
WEB_ECR_ARN := 160358319781.dkr.ecr.eu-west-1.amazonaws.com
VERSION := build-$(shell date +%Y%m%dT%H%M%SZ)
LATEST_TAG := latest

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

#################
# Reach Scraper #
#################

.PHONY: scraper-image
scraper-image: base-image
	docker build \
		-t $(ECR_ARN)/reach-scraper:$(VERSION) \
		-t $(ECR_ARN)/reach-scraper:$(LATEST_TAG) \
		-f pipeline/reach-scraper/Dockerfile \
		./pipeline/reach-scraper

.PHONY: push-scraper
push-scraper: scraper-image
	$$(aws ecr get-login --no-include-email --region eu-west-1) && \
		docker push $(ECR_ARN)/reach-scraper:$(LATEST_TAG) && \
		docker push $(ECR_ARN)/reach-scraper:$(VERSION)

################
# Reach Parser #
################

.PHONY: parser-image
parser-image: base-image
	docker build \
		-t $(ECR_ARN)/reach-parser:$(VERSION) \
		-t $(ECR_ARN)/reach-parser:$(LATEST_TAG) \
		-f pipeline/reach-parser/Dockerfile \
		./pipeline/reach-parser

.PHONY: push-parser
push-parser: parser-image
	$$(aws ecr get-login --no-include-email --region eu-west-1) && \
		docker push $(ECR_ARN)/reach-parser:$(LATEST_TAG) && \
		docker push $(ECR_ARN)/reach-parser:$(VERSION)

###################
# Reach Extractor #
###################

.PHONY: es-extracter-image
es-extracter-image: base-image
	docker build \
		-t $(ECR_ARN)/reach-es-extractor:$(VERSION) \
		-t $(ECR_ARN)/reach-es-extractor:$(LATEST_TAG) \
		-f pipeline/reach-es-extractor/Dockerfile \
		./pipeline/reach-es-extractor

.PHONY: push-extracter
push-extracter: es-extracter-image
	$$(aws ecr get-login --no-include-email --region eu-west-1) && \
		docker push $(ECR_ARN)/reach-es-extractor:$(LATEST_TAG) && \
		docker push $(ECR_ARN)/reach-es-extractor:$(VERSION)

#################
# Reach Indexer #
#################

.PHONY: indexer-image
indexer-image: base-image
	docker build \
		-t $(ECR_ARN)/reach-es-indexer:$(VERSION) \
		-t $(ECR_ARN)/reach-es-indexer:$(LATEST_TAG) \
		-f pipeline/reach-es-indexer/Dockerfile \
		./pipeline/reach-es-indexer

.PHONY: push-indexer
push-indexer: indexer-image
	$$(aws ecr get-login --no-include-email --region eu-west-1) && \
		docker push $(ECR_ARN)/reach-es-indexer:$(LATEST_TAG) && \
		docker push $(ECR_ARN)/reach-es-indexer:$(VERSION)


######################
# Reach FuzzyMatcher #
######################

.PHONY: fuzzymatcher-image
fuzzymatcher-image: base-image
	docker build \
		-t $(ECR_ARN)/reach-fuzzy-matcher:$(VERSION) \
		-t $(ECR_ARN)/reach-fuzzy-matcher:$(LATEST_TAG) \
		-f pipeline/reach-fuzzy-matcher/Dockerfile \
		./pipeline/reach-fuzzy-matcher

.PHONY: push-fuzzymatcher
push-fuzzymatcher: fuzzymatcher-image
	$$(aws ecr get-login --no-include-email --region eu-west-1) && \
		docker push $(ECR_ARN)/reach-fuzzy-matcher:$(LATEST_TAG) && \
		docker push $(ECR_ARN)/reach-fuzzy-matcher:$(VERSION)

#############
# Reach Web #
#############

.PHONY: reach-web-build
reach-web-build:
	docker build \
		-t reach-web-build:$(VERSION) \
		-t reach-web-build:$(LATEST_TAG) \
		-f web/Dockerfile.node \
		./web


.PHONY: build-web-static
build-web-static: reach-web-build
	@chmod +x web/bin/docker_run.sh
	@mkdir -p web/build/web/static
	web/bin/docker_run.sh gulp default



.PHONY: web-image
web-image: base-image build-web-static
	docker build \
		-t $(WEB_ECR_ARN)/${WEB_IMAGE}:$(VERSION) \
		-t $(WEB_ECR_ARN)/${WEB_IMAGE}:$(LATEST_TAG) \
		-f web/Dockerfile \
		./web

.PHONY: push-web
push-web: web-image
	$$(aws ecr get-login --no-include-email --region eu-west-1) && \
		docker push $(WEB_ECR_ARN)/${WEB_IMAGE}:$(LATEST_TAG) && \
		docker push $(WEB_ECR_ARN)/${WEB_IMAGE}:$(VERSION)


##############
# Local runs #
##############

.PHONY: run-scraper
run-scraper: scraper-image
	docker run \
	    -e AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID}" \
		-e AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY}" \
		-e SENTRY_DSN="${SENTRY_DSN}" \
	    ${ECR_ARN}/reach-scraper \
		${SCRAPER_DST} \
		${ORG}


.PHONY: run-parser
run-parser: parser-image
	docker run \
	  -e AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID}" \
		-e AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY}" \
		-e SENTRY_DSN="${SENTRY_DSN}" \
	    ${ECR_ARN}/reach-parser \
		${SCRAPER_DST} \
		${PARSER_DST} \
		${ORG}


.PHONY: run-extracter
run-extracter: es-extracter-image
	docker run \
	  -e AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID}" \
		-e AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY}" \
		-e SENTRY_DSN="${SENTRY_DSN}" \
	    ${ECR_ARN}/reach-es-extractor \
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
		${ECR_ARN}/reach-es-indexer \
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
		${ECR_ARN}/reach-indexer \
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
		${ECR_ARN}/reach-fuzzymatcher \
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
		${ECR_ARN}/reach-es-indexer \
		${FUZZYMATCHER_DST} \
		${ORG} \
		citations


.PHONY: docker-run
docker-run: docker-build run-scraper run-parser run-extracter run-indexer-epmc run-indexer-citations



##################
# Testing images #
##################

.PHONY: scraper-tests-image
scraper-tests-image: base-image
	docker build \
		-t $(ECR_ARN)/test-reach-scraper:$(LATEST_TAG) \
		-f pipeline/reach-scraper/Dockerfile.test \
		./pipeline/reach-scraper

.PHONY: test-scraper
test-scraper: scraper-tests-image
	docker run -u root \
		-e SENTRY_DSN="${SENTRY_DSN}" \
		--rm $(ECR_ARN)/test-reach-scraper:latest \
		sh -c "pip install pytest && pytest /opt/reach/"

.PHONY: parser-tests-image
parser-tests-image: base-image
	docker build \
		-t $(ECR_ARN)/test-reach-parser:$(LATEST_TAG) \
		-f pipeline/reach-parser/Dockerfile.test \
		./pipeline/reach-parser

.PHONY: test-parser
test-parser: parser-tests-image
	docker run -u root \
		-e SENTRY_DSN="${SENTRY_DSN}" \
		--rm $(ECR_ARN)/test-reach-parser:latest \
		sh -c "pip install pytest && pytest /opt/reach/"

.PHONY: extractor-tests-image
extractor-tests-image: base-image
	docker build \
		-t $(ECR_ARN)/test-reach-extractor:$(LATEST_TAG) \
		-f pipeline/reach-es-extractor/Dockerfile.test \
		./pipeline/reach-es-extractor

.PHONY: test-extractor
test-extractor: extractor-tests-image
	docker run -u root \
		-e SENTRY_DSN="${SENTRY_DSN}" \
		--rm $(ECR_ARN)/test-reach-extractor:latest \
		sh -c "pip install pytest && pytest /opt/reach/"

###################
# General recipes #
###################

.PHONY: docker-test
docker-test: test-scraper test-parser test-extractor

.PHONY: docker-build
docker-build: base-image scraper-image parser-image es-extracter-image indexer-image fuzzymatcher-image

.PHONY: docker-push-all
docker-push-all: docker-test push-fuzzymatcher push-extracter push-indexer push-parser push-scraper

.PHONY: all
all: docker-build
