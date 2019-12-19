.DEFAULT_GOAL := all

VIRTUALENV := build/virtualenv

IMAGE := uk.ac.wellcome/reach
ECR_IMAGE := 160358319781.dkr.ecr.eu-west-1.amazonaws.com/$(IMAGE)
LATEST_TAG := latest
VERSION := latest

#
# Wheel for deep_reference_parser
#

DEEP_REFERENCE_PARSER_WHEEL := deep_reference_parser-2019.12.1-py3-none-any.whl
DEEP_REFERENCE_PARSER_URL := https://datalabs-public.s3.eu-west-2.amazonaws.com/deep_reference_parser/$(DEEP_REFERENCE_PARSER_WHEEL)

SPACY_MODEL_URL := https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-2.1.0/en_core_web_sm-2.1.0.tar.gz#egg=en_core_web_sm==2.1.0
KERAS_CONTRIB_URL := https://github.com/keras-team/keras-contrib/tarball/master

#
# reach/web
#

WEB_BUILD_IMAGE := reach-web-build
WEB_BUILD_SOURCES := \
	reach/web/src/css/style.css \
	reach/web/gulpfile.js \
	reach/web/src/js/app.js

WEB_BUILD_TARGETS := \
 	build/web/static/css/style.css \
 	build/web/static/js/main.js

# Image used for building web static assets
.PHONY: web-build-image
web-build-image:
	docker build \
		-t $(WEB_BUILD_IMAGE):latest \
		-f reach/web/Dockerfile.node \
		reach/web/


# NB: our target will run every time b/c web-build-image is
# a phony target. Not great but we don't need incremental builds
# for static web sources.
$(WEB_BUILD_TARGETS): web-build-image $(WEB_BUILD_SOURCES)
	@# CodePipeline (but not CodeBuild) code checkouts lose execution bits
	@# (https://forums.aws.amazon.com/thread.jspa?threadID=235452).
	@# So, fix this for CI builds.
	@chmod +x reach/web/bin/docker_run.sh
	@mkdir -p build/web/static
	reach/web/bin/docker_run.sh gulp default


#
# docker build for $(ECR_IMAGE):$(VERSION)
#

# Tags to use when run within codebuild.
#
# codebuild-${ISO8601}-${SHA_PREFIX}
CODEBUILD_VERSION := codebuild-$(shell date +%Y%m%dT%H%M%SZ)-$(shell \
	echo $$CODEBUILD_RESOLVED_SOURCE_VERSION | cut -c1-7)
CODEBUILD_LATEST_TAG := codebuild-latest

.PHONY: base-image
base-image:
	docker build \
		-t reach.base \
		-f Dockerfile.base \
		.

.PHONY: docker-build
docker-build: base-image $(WEB_BUILD_TARGETS)
	docker build \
		-t $(ECR_IMAGE):$(VERSION) \
		-t $(ECR_IMAGE):$(LATEST_TAG) \
		.

.PHONY: docker-push
docker-push: docker-test
	$$(aws ecr get-login --no-include-email --region eu-west-1) && \
	docker push $(ECR_IMAGE):$(VERSION) && \
	docker push $(ECR_IMAGE):$(LATEST_TAG)

#
# build/virtualenv (for docker-less dev)
#

$(VIRTUALENV)/.installed: requirements.txt test_requirements.txt $(REFERENCE_SPLITTER_WHEEL)
	@if [ -d $(VIRTUALENV) ]; then rm -rf $(VIRTUALENV); fi
	@mkdir -p $(VIRTUALENV)
	virtualenv --python python3 $(VIRTUALENV)
	AIRFLOW_GPL_UNIDECODE=yes $(VIRTUALENV)/bin/pip3 install -r requirements.txt
	$(VIRTUALENV)/bin/pip3 install -r test_requirements.txt
	$(VIRTUALENV)/bin/pip3 install $(DEEP_REFERENCE_PARSER_URL)
	$(VIRTUALENV)/bin/python setup.py develop --no-deps
	touch $@

# Builds, tests, & pushes docker images with CodeBuild specific VERSION
# and LATEST_TAG.
.PHONY: codebuild-docker-push
codebuild-docker-push: VERSION := $(CODEBUILD_VERSION)
codebuild-docker-push: LATEST_TAG := $(CODEBUILD_LATEST_TAG)
codebuild-docker-push: docker-push

.PHONY: virtualenv
virtualenv: $(VIRTUALENV)/.installed

.PHONY: update-requirements-txt
update-requirements-txt: VIRTUALENV := /tmp/update-requirements-txt
update-requirements-txt: 
	if [ -d $(VIRTUALENV) ]; then \
		rm -rf $(VIRTUALENV); \
	fi
	virtualenv --python python3 $(VIRTUALENV)
	$(VIRTUALENV)/bin/pip3 install -r unpinned_requirements.txt
	# Install deep_reference_parser here so that we can track the
	# dependencies it pulls in.
	$(VIRTUALENV)/bin/pip3 install $(DEEP_REFERENCE_PARSER_URL)
	echo "# Created by 'make update-requirements-txt'. DO NOT EDIT!" > requirements.txt
	# ... and then make sure its full URL is used in the output
	$(VIRTUALENV)/bin/pip freeze | grep -v pkg-resources==0.0.0 | \
		grep -v deep-reference-parser | grep -v en-core-web-sm | \
		grep -v keras-contrib | \
		sed 's/airflow/airflow[celery]/' >> requirements.txt 
	echo $(SPACY_MODEL_URL) >> requirements.txt
	echo $(KERAS_CONTRIB_URL) >> requirements.txt
	echo $(DEEP_REFERENCE_PARSER_URL) >> requirements.txt


#
# testing
#

.PHONY: test
test: virtualenv
	$(VIRTUALENV)/bin/pytest -s ./reach

.PHONY: docker-test
docker-test: docker-build
	docker run -u root -v $$(pwd)/test_requirements.txt:/test_requirements.txt \
		--rm $(ECR_IMAGE):$(VERSION) \
		sh -c "pip3 install -r /test_requirements.txt && pytest /opt/reach"



.PHONY: all
all: docker-test

