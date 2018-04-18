# Use a basic Python image
FROM python:3.6.4

# Poppler is needed to run pdftotext convertion
RUN apt-get update -yqq \
  && apt-get install -yqq --no-install-recommends \
    gcc \
    libpoppler-cpp-dev \
    poppler-utils \
    pkg-config \
    locales \
  && apt-get -q clean

# Build locales to avoid encoding issues with Scrapy encoding
RUN locale-gen en_GB.UTF-8

ENV LC_ALL=en_GB.UTF-8
ENV LANG=en_GB.UTF-8
ENV LANGUAGE=en_GB.UTF-8

WORKDIR /wsf_scraper

COPY ./wsf_scraping /wsf_scraper/wsf_scraping
COPY ./resources /wsf_scraper/resources
COPY ./pdf_parser /wsf_scraper/pdf_parser
COPY ./tools /wsf_scraper/tools

COPY ./api.py /wsf_scraper/api.py

COPY ./scrapy.cfg /wsf_scraper/scrapy.cfg
COPY ./requirements.txt /wsf_scraper/requirements.txt

# Scrapy needs a var directory to store logs
RUN mkdir var

RUN pip install -r requirements.txt

EXPOSE 5005

CMD ["python", "api.py"]
