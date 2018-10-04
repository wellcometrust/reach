.DEFAULT_GOAL := all

IMAGE := uk.ac.wellcome/web-scraper
VERSION := 2018.10.0

.PHONY: base_image
base_image:
	docker build -t web-scraper.base -f Dockerfile.base .

.PHONY: image
image:
	docker build -t $(IMAGE):$(VERSION) .

.PHONY: all
all: base_image image
