# Use a basic Python image
FROM reach.base

COPY setup.py /src/reach/
COPY README.md /src/reach/
COPY unpinned_requirements.txt /src/reach/
COPY reach/ /src/reach/reach/

# Airflow deps
COPY reach/scrapy.cfg /etc/scraper/scrapy.cfg

COPY build/web/ /build/web/
ENV STATIC_ROOT=/build/web/static

# TODO: cd /src after we've moved setup.py up a dir
RUN /bin/sh -c 'cd /src/reach && python3 setup.py develop --no-deps'

# Airflow
COPY reach/airflow/airflow.cfg /airflow/
COPY reach/airflow/initdb.sh /airflow/
RUN mkdir -p /airflow/db && \
    ln -s /src/reach/reach/airflow/dags /airflow/dags && \
    chmod +x /airflow/initdb.sh && \
    chown -R www-data: /airflow

USER www-data
