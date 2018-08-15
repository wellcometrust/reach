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

WORKDIR /wsf_scraper

COPY ./wsf_scraping /wsf_scraper/wsf_scraping
COPY ./resources /wsf_scraper/resources
COPY ./pdf_parser /wsf_scraper/pdf_parser
COPY ./tools /wsf_scraper/tools

COPY ./entrypoint.sh /wsf_scraper/entrypoint.sh

COPY ./scrapy.cfg /wsf_scraper/scrapy.cfg

# Pipenv require these two files to install requirements in the pinned version
COPY ./Pipfile /wsf_scraper/Pipfile
COPY ./Pipfile.lock /wsf_scraper/Pipfile.lock

# Scrapy needs a var directory to store logs
RUN mkdir -p var/tmp

# Install dependencies using pipenv
RUN pip install -U pip
RUN pip install pipenv
RUN pipenv install --system --deploy

CMD ["./entrypoint.sh"]
