.DEFAULT_GOAL := all

VIRTUALENV := build/virtualenv

IMAGE := uk.ac.wellcome/reference-parser
ECR_IMAGE := 160358319781.dkr.ecr.eu-west-1.amazonaws.com/$(IMAGE)
VERSION := 2019.2.2

# Tags to use when run within codebuild.
#
# codebuild-${ISO8601}-${SHA_PREFIX}
CODEBUILD_VERSION := codebuild-$(shell date +%Y%m%dT%H%M%SZ)-$(shell \
	echo $$CODEBUILD_RESOLVED_SOURCE_VERSION | cut -c1-7)
CODEBUILD_LATEST_TAG := codebuild-latest

.PHONY: docker-build
docker-build:
	docker build \
		-t $(IMAGE):$(VERSION) \
		-t $(IMAGE):latest \
		-t $(ECR_IMAGE):$(VERSION) \
		-t $(ECR_IMAGE):latest \
		.

.PHONY: docker-push
push: docker-test
	$$(aws ecr get-login --no-include-email --region eu-west-1) && \
	docker push $(ECR_IMAGE):$(VERSION) && \
	docker push $(ECR_IMAGE):latest

$(VIRTUALENV)/.installed: requirements.txt
	@if [ -d $(VIRTUALENV) ]; then rm -rf $(VIRTUALENV); fi
	@mkdir -p $(VIRTUALENV)
	virtualenv --python python3 $(VIRTUALENV)
	$(VIRTUALENV)/bin/pip3 install -r requirements.txt
	touch $@

# Builds, tests, & pushes docker images with CodeBuild specific VERSION
# and LATEST_TAG.
.PHONY: codebuild-docker-push
codebuild-docker-push: VERSION := $(CODEBUILD_VERSION)
codebuild-docker-push: LATEST_TAG := $(CODEBUILD_LATEST_TAG)
codebuild-docker-push: docker-push

.PHONY: virtualenv
virtualenv: $(VIRTUALENV)/.installed

.PHONY: docker-test
docker-test: docker-build
	docker run -v $$(pwd)/requirements.txt:/requirements.txt \
	    --rm $(ECR_IMAGE):$(VERSION) \
		sh -c "pip3 install -r requirements.txt && python3 -m unittest"

.PHONY: all
all: docker-build
