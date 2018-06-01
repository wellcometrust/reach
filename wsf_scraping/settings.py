# -*- coding: utf-8 -*-
import logging
import os

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
    'aws': 'tools.AWSFeedStorage',
}

LOG_LEVEL = 'INFO'
LOG_FORMATTER = 'wsf_scraping.middlewares.PoliteLogFormatter'

# Set pdfminer log to WARNING
logging.getLogger("pdfminer").setLevel(logging.WARNING)

DUPEFILTER_CLASS = 'scrapy.dupefilters.BaseDupeFilter'
# Use a physicqal queue, slower but add fiability
DEPTH_PRIORITY = 1
SCHEDULER_DISK_QUEUE = 'scrapy.squeues.PickleFifoDiskQueue'

# Crawl responsibly by identifying yourself (and your website)
USER_AGENT = 'wsf_scraping'

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

#  who_iris and who_iris_single_page dedicated settings
WHO_IRIS_RPP = 250
WHO_IRIS_LIMIT = False
WHO_IRIS_YEARS = [2012, 2013, 2014, 2015, 2016, 2017]

# nice dedicated settings
NICE_GET_HISTORY = False
NICE_GET_EVIDENCES = False
NICE_ARTICLES_COUNT = -1

# Wether or not keep the PDF on a keyword match
PARSING_METHOD = 'pdftotext'  # pdftotext|pdfminer
KEEP_PDF = False
DOWNLOAD_ONLY = False
KEYWORDS_CONTEXT = 0

# Jsonlines are cleaner for big feeds
FEED_FORMAT = 'jsonlines'
FEED_EXPORT_ENCODING = 'utf-8'
FEED_TEMPDIR = 'var/tmp/'

if FEED_CONFIG == 'AWS':
    AWS_S3_BUCKET = 'datalabs-data'
    AWS_S3_FILE_NAME = 'scraper-results/%(name)s'
    DATABASE_ADAPTOR = 'dynamodb'
    FEED_URI = 'aws://{bucket}/{filename}'.format(
        bucket=AWS_S3_BUCKET,
        filename=AWS_S3_FILE_NAME
    )

else:
    # By default, log the results in a local folder
    DATABASE_ADAPTOR = 'postgresql'
    FEED_URI = './results/%(name)s.json'

# Lists to look for (case insensitive)
SECTIONS_KEYWORDS_FILE = './resources/section_keywords.txt'

# Keywords to look for (case insensitive)
KEYWORDS_FILE = './resources/keywords.txt'
