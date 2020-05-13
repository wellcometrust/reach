# Use a basic Python image, but current Debian
FROM python:3.6-slim-stretch

# Build UTF8 locale to avoid encoding issues with Scrapy encoding
# C.UTF-8 is the new en_US.UTF-8.
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
ENV LANGUAGE=C.UTF-8

WORKDIR /opt/reach

COPY ./requirements.txt /opt/reach/requirements.txt

# Poppler is needed to run pdftotext convertion
RUN apt-get update -yqq && \
apt-get install -yqq --no-install-recommends \
        build-essential \
        libpoppler-cpp-dev \
        poppler-utils \
        locales && \
    apt-get -q clean && \
    locale-gen C.UTF-8 && \
    pip install -U pip && \
    python3 -m pip install -r /opt/reach/requirements.txt && \
    apt-get remove --purge -y build-essential


COPY ./safe_import.py /opt/reach/safe_import.py
COPY ./hooks /opt/reach/hooks
COPY ./elastic /opt/reach/elastic
COPY ./tests /opt/reach/tests
