FROM reach.base

WORKDIR /opt/scraper

COPY ./requirements.txt /opt/scraper/requirements.txt
COPY ./scrapy.cfg /etc/scraper/scrapy.cfg
COPY ./spider_task.py /opt/scraper/spider_task.py
COPY ./wsf_scraping /opt/scraper/wsf_scraping

# Put the generic sentry.py file in the right module
RUN mv /opt/reach/sentry.py /opt/scraper/sentry.py

# Give execution rights to the entrypoint Python script
RUN chmod +x /opt/scraper/spider_task.py

ENTRYPOINT ["/opt/scraper/spider_task.py"]
