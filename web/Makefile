.DEFAULT_GOAL := all

# Web application
.PHONY: docker-build
docker-build:
	docker build \
	    -t uk.ac.wellcome/reach/web \
		-f Dockerfile \
		.

.PHONY: all
all: docker-build
