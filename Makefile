.DEFAULT_GOAL := all

IMAGE := uk.ac.wellcome/reference-parser
ECR_IMAGE := 160358319781.dkr.ecr.eu-west-1.amazonaws.com/$(IMAGE)
VERSION := 2018.10.0

.PHONY: image
image:
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

.PHONY: all
all: image
