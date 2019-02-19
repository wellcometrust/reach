# Use a basic Python image
FROM web-scraper.base


# TODO: copy policytool/ or such once we're one dir up
COPY setup.py /src/policytool/
COPY README.md /src/policytool/
COPY scraper/ /src/policytool/scraper/

COPY ./entrypoint.sh /entrypoint.sh

COPY ./scrapy.cfg /etc/scraper/scrapy.cfg

# TODO: cd /src after we've moded setup.py up a dir
RUN /bin/sh -c 'cd /src/policytool && python3 setup.py develop --no-deps'

# COPY datalabs/airflow/airflow.cfg /airflow/
# COPY datalabs/airflow/initdb.sh /airflow/
RUN mkdir -p /airflow/db
RUN ln -s /src/policytool/scraper/airflow/dags /airflow/dags

CMD ["/entrypoint.sh"]
