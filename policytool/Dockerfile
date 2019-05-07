# Use a basic Python image
FROM web-scraper.base

COPY setup.py /src/policytool/
COPY README.md /src/policytool/

# Airflow deps
COPY scraper/ /src/policytool/scraper/
COPY pdf_parser/ /src/policytool/pdf_parser/
COPY ./scrapy.cfg /etc/scraper/scrapy.cfg

# Web deps
COPY web/ /src/policytool/web/
ENV STATIC_ROOT=/src/policytool/web/build/static

# TODO: cd /src after we've moved setup.py up a dir
RUN /bin/sh -c 'cd /src/policytool && python3 setup.py develop --no-deps'

# Airflow
COPY scraper/airflow/airflow.cfg /airflow/
COPY scraper/airflow/initdb.sh /airflow/
RUN mkdir -p /airflow/db && \
    ln -s /src/policytool/scraper/airflow/dags /airflow/dags && \
    chmod +x /airflow/initdb.sh && \
    chown -R www-data: /airflow


USER www-data
