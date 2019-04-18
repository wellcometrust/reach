# Use a basic Python image
FROM web-scraper.base

COPY setup.py /src/policytool/
COPY README.md /src/policytool/
COPY scraper/ /src/policytool/scraper/
COPY pdf_parser/ /src/policytool/pdf_parser/
COPY web/ /src/policytool/web/

COPY ./scrapy.cfg /etc/scraper/scrapy.cfg

# TODO: cd /src after we've moved setup.py up a dir
RUN /bin/sh -c 'cd /src/policytool && python3 setup.py develop --no-deps'

# Airflow
COPY scraper/airflow/airflow.cfg /airflow/
COPY scraper/airflow/initdb.sh /airflow/
RUN mkdir -p /airflow/db && \
    ln -s /src/policytool/scraper/airflow/dags /airflow/dags && \
    chown -R www-data: /airflow

USER www-data
