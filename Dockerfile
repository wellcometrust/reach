# Use a basic Python image
FROM policytool.base

COPY setup.py /src/policytool/
COPY README.md /src/policytool/
COPY unpinned_requirements.txt /src/policytool/
COPY policytool/ /src/policytool/policytool/

# Airflow deps
COPY policytool/scrapy.cfg /etc/scraper/scrapy.cfg

COPY build/web/ /build/web/
ENV STATIC_ROOT=/build/web/static

# TODO: cd /src after we've moved setup.py up a dir
RUN /bin/sh -c 'cd /src/policytool && python3 setup.py develop --no-deps'

# Airflow
COPY policytool/airflow/airflow.cfg /airflow/
COPY policytool/airflow/initdb.sh /airflow/
RUN mkdir -p /airflow/db && \
    ln -s /src/policytool/policytool/airflow/dags /airflow/dags && \
    chmod +x /airflow/initdb.sh && \
    chown -R www-data: /airflow

USER www-data
