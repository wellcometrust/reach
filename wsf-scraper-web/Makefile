.DEFAULT_GOAL := all

VIRTUALENV := build/virtualenv

IMAGE := uk.ac.wellcome/web-scraper
ECR_IMAGE := 160358319781.dkr.ecr.eu-west-1.amazonaws.com/$(IMAGE)
VERSION := 2019.1.1

.PHONY: base_image
base_image:
	docker build -t web-scraper.base -f Dockerfile.base .

.PHONY: image
image: base_image
	docker build \
		-t $(IMAGE):$(VERSION) \
		-t $(IMAGE):latest \
		-t $(ECR_IMAGE):$(VERSION) \
		-t $(ECR_IMAGE):latest \
		.

.PHONY: push
push: image
	$$(aws ecr get-login --no-include-email --region eu-west-1) && \
	docker push $(ECR_IMAGE):$(VERSION) && \
	docker push $(ECR_IMAGE):latest

$(VIRTUALENV)/.installed: requirements.txt
	@if [ -d $(VIRTUALENV) ]; then rm -rf $(VIRTUALENV); fi
	@mkdir -p $(VIRTUALENV)
	virtualenv --python python3 $(VIRTUALENV)
	$(VIRTUALENV)/bin/pip3 install -r requirements.txt
	touch $@

.PHONY: virtualenv
virtualenv: $(VIRTUALENV)/.installed

.PHONY: all
all: base_image image
