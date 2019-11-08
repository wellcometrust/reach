# Use a basic Python image
FROM reach.base

COPY setup.py /opt/reach
COPY README.md /opt/reach
COPY unpinned_requirements.txt /opt/reach
COPY reach/ /opt/reach/reach/

# Airflow deps
COPY reach/scrapy.cfg /etc/scraper/scrapy.cfg

COPY build/web/ /opt/reach/build/web/
ENV STATIC_ROOT=/opt/reach/build/web/static

# TODO: cd /src after we've moved setup.py up a dir
RUN /bin/sh -c 'cd /opt/reach && python3 setup.py develop --no-deps'

# Airflow
COPY reach/airflow/airflow.cfg /opt/airflow/
COPY reach/airflow/initdb.sh /opt/airflow/
RUN mkdir -p /opt/airflow/db && \
    ln -s /opt/reach/reach/airflow/dags /opt/airflow/dags && \
    chmod +x /opt/airflow/initdb.sh && \
    mkdir -p /opt/airflow/logs && \
    chmod -R 777 /opt/airflow/logs && \
    chown -R www-data: /opt/airflow

USER www-data
