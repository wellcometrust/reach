# -*- coding: utf-8 -*-
import logging
import os
from datetime import datetime

# Get feed configuration from environment variable. Default to debug
FEED_CONFIG = os.environ.get('SCRAPY_FEED_CONFIG', 'DEBUG')
BOT_NAME = 'wsf_scraper'

SPIDER_MODULES = ['wsf_scraping.spiders']
NEWSPIDER_MODULE = 'wsf_scraping.spiders'

# Custom contrats for spider testing
SPIDER_CONTRACTS = {
    'wsf_scraping.contracts.AjaxContract': 10,
}
ITEM_PIPELINES = {
    'wsf_scraping.pipelines.WsfScrapingPipeline': 10,
}
FEED_STORAGES = {
    'manifests3': 'wsf_scraping.feed_storage.ManifestFeedStorage',
    'local': 'wsf_scraping.feed_storage.ManifestFeedStorage',
}

SPIDER_MIDDLEWARES = {
    'wsf_scraping.middlewares.ReachDisallowedHostMiddleware': 450,
}

LOG_LEVEL = 'INFO'
LOG_FORMATTER = 'wsf_scraping.middlewares.PoliteLogFormatter'

# Set pdfminer log to WARNING
logging.getLogger("pdfminer").setLevel(logging.WARNING)

DUPEFILTER_CLASS = 'scrapy.dupefilters.RFPDupeFilter'
# Use a physicqal queue, slower but add fiability
DEPTH_PRIORITY = 1
SCHEDULER_DISK_QUEUE = 'scrapy.squeues.PickleFifoDiskQueue'

# Crawl responsibly by identifying yourself (and your website)
USER_AGENT = 'Wellcome Reach Scraper (datalabs-ops@wellcome.ac.uk)'

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 5
CONCURRENT_REQUESTS_PER_DOMAIN = 5
RETRY_ENABLED = True
RETRY_TIMES = 3
DOWNLOAD_WARNSIZE = 0
DOWNLOAD_MAXSIZE = 0
DOWNLOAD_TIMEOUT = 20
DOWNLOAD_FAIL_ON_DATALOSS = True
DOWNLOAD_DELAY = 0.25

HTTPCACHE_ENABLED = False

AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 0.1
AUTOTHROTTLE_MAX_DELAY = 0.5
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0

# Disable cookies
COOKIES_ENABLED = False

MAX_ARTICLE = int(os.environ.get('MAX_ARTICLE', '-1'))

#  who_iris and who_iris_single_page dedicated settings
WHO_IRIS_RPP = 250
WHO_IRIS_LIMIT = False
if 'WHO_IRIS_YEARS' in os.environ:
    WHO_IRIS_YEARS = [
        int(x) for x in os.environ['WHO_IRIS_YEARS'].split(',')
    ]
else:
    WHO_IRIS_YEARS = list(range(2012, datetime.now().year + 1))

# nice dedicated settings
NICE_GET_HISTORY = False
NICE_GET_EVIDENCES = False

KEYWORDS_CONTEXT = 0

# Jsonlines are cleaner for big feeds
FEED_FORMAT = 'jsonlines'
FEED_EXPORT_ENCODING = 'utf-8'
FEED_TEMPDIR = '/tmp/'

# By default, log the results in a local folder
FEED_URI = os.environ.get('SCRAPY_FEED_URI', 'local:///tmp/%(name)s')

DATABASE_URL = os.environ.get('DATABASE_URL')
