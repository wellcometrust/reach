.DEFAULT_GOAL := all

VIRTUALENV := build/virtualenv

IMAGE := uk.ac.wellcome/web-scraper
ECR_IMAGE := 160358319781.dkr.ecr.eu-west-1.amazonaws.com/$(IMAGE)
VERSION := latest


# Tags to use when run within codebuild.
#
# codebuild-${ISO8601}-${SHA_PREFIX}
CODEBUILD_VERSION := codebuild-$(shell date +%Y%m%dT%H%M%SZ)-$(shell \
	echo $$CODEBUILD_RESOLVED_SOURCE_VERSION | cut -c1-7)
CODEBUILD_LATEST_TAG := codebuild-latest

.PHONY: base-image
base-image:
	docker build -t web-scraper.base -f Dockerfile.base .

.PHONY: docker-build
docker-build: base-image
	docker build \
		-t $(ECR_IMAGE):$(VERSION) \
		-t $(ECR_IMAGE):latest \
		.

.PHONY: docker-push
docker-push: docker-test
	$$(aws ecr get-login --no-include-email --region eu-west-1) && \
	docker push $(ECR_IMAGE):$(VERSION) && \
	docker push $(ECR_IMAGE):latest

# Builds, tests, & pushes docker images with CodeBuild specific VERSION
# and LATEST_TAG.
.PHONY: codebuild-docker-push
codebuild-docker-push: VERSION := $(CODEBUILD_VERSION)
codebuild-docker-push: LATEST_TAG := $(CODEBUILD_LATEST_TAG)
codebuild-docker-push: docker-push

$(VIRTUALENV)/.installed: requirements.txt test_requirements.txt
	@if [ -d $(VIRTUALENV) ]; then rm -rf $(VIRTUALENV); fi
	@mkdir -p $(VIRTUALENV)
	virtualenv --python python3 $(VIRTUALENV)
	AIRFLOW_GPL_UNIDECODE=yes $(VIRTUALENV)/bin/pip3 install -r requirements.txt
	$(VIRTUALENV)/bin/pip3 install -r test_requirements.txt
	$(VIRTUALENV)/bin/python setup.py develop --no-deps
	touch $@

.PHONY: virtualenv
virtualenv: $(VIRTUALENV)/.installed


.PHONY: test
test: virtualenv
	$(VIRTUALENV)/bin/pytest ./

.PHONY: docker-test
docker-test: docker-build
	docker run -u root -v $$(pwd)/test_requirements.txt:/test_requirements.txt \
		--rm $(ECR_IMAGE):$(VERSION) \
		sh -c "pip3 install -r /test_requirements.txt && pytest /src/policytool"


#
# Tooling for updating requirements.txt, b/c $(VIRTUALENV) also has test
# dependencies in it.
#
.PHONY: update-requirements-txt
update-requirements-txt: VIRTUALENV := /tmp/update-requirements-txt
update-requirements-txt:
	if ! [ -d $(VIRTUALENV) ]; then \
		mkdir -p $(VIRTUALENV) && \
		virtualenv --python python3.6 $(VIRTUALENV) && \
		AIRFLOW_GPL_UNIDECODE=yes $(VIRTUALENV)/bin/pip3 install -r requirements.txt ; \
	fi
	echo "# Created by 'make update-requirements-txt'. DO NOT EDIT!" > requirements.txt
	$(VIRTUALENV)/bin/pip freeze | grep -v pkg-resources==0.0.0 | \
		sed 's/airflow/airflow[celery]/' >> requirements.txt



.PHONY: all
all: docker-test
