# -*- coding: utf-8 -*-
import datetime
import logging
import os

# Scrapy settings for wsf_scraping project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#     http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
#     http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html

# Get feed configuration from environment variable. Default to debug
FEED_CONFIG = os.environ.get('SCRAPY_FEED_CONFIG', 'DEBUG')
BOT_NAME = 'wsf_scraper'

SPIDER_MODULES = ['wsf_scraping.spiders']
NEWSPIDER_MODULE = 'wsf_scraping.spiders'

# Custom contrats for spider testing
ITEM_PIPELINES = {
    'wsf_scraping.pipelines.WsfScrapingPipeline': 10,
}
FEED_STORAGES = {
    'dsx': 'tools.DSXFeedStorage.DSXFeedStorage',
}

# LOG_ENABLED = False
LOG_LEVEL = 'INFO'
LOG_FILE = 'var/log-{log_level}.txt'.format(log_level=LOG_LEVEL)
LOG_STDOUT = True
# Set pdfminer log to WARNING
logging.getLogger("pdfminer").setLevel(logging.WARNING)

# Use a physical queue, slower but add fiability
DEPTH_PRIORITY = 1
SCHEDULER_DISK_QUEUE = 'scrapy.squeues.PickleFifoDiskQueue'
SCHEDULER_MEMORY_QUEUE = 'scrapy.squeues.FifoMemoryQueue'
DUPEFILTER_CLASS = "wsf_scraping.filter.BLOOMDupeFilter"

# Crawl responsibly by identifying yourself (and your website)
# USER_AGENT = 'wsf_scraping (+wateystrdjytkfu)'

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 8
CONCURRENT_REQUESTS_PER_DOMAIN = 8
RETRY_ENABLED = True
RETRY_TIMES = 3
DOWNLOAD_WARNSIZE = 0
DOWNLOAD_MAXSIZE = 0
DOWNLOAD_TIMEOUT = 20
DOWNLOAD_FAIL_ON_DATALOSS = True

SCHEDULER_MEMORY_QUEUE = 'scrapy.squeues.FifoMemoryQueue'

HTTPCACHE_ENABLED = False

AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 0.1
AUTOTHROTTLE_MAX_DELAY = 0.5
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0

# Disable cookies
COOKIES_ENABLED = False

#  who_iris and who_iris_single_page dedicated settings
WHO_IRIS_RPP = 250
WHO_IRIS_YEARS = [2012]
WHO_IRIS_LIMIT = False
# WHO_IRIS_YEARS = [2012, 2013, 2014, 2015, 2016, 2017]

# Wether or not keep the PDF on a keyword match
KEEP_PDF = False
DOWNLOAD_ONLY = False
KEYWORDS_CONTEXT = 0

# Jsonlines are cleaner for big feeds
FEED_FORMAT = 'jsonlines'
FEED_EXPORT_ENCODING = 'utf-8'
FEED_TEMPDIR = 'var/tmp/'

if FEED_CONFIG == 'S3':
    AWS_ACCESS_KEY_ID = ''
    AWS_SECRET_ACCESS_KEY = ''
    AWS_FEED_CONTAINER = ''
    FEED_URI = 's3://' + AWS_FEED_CONTAINER + '/%(name)s - %(time)s.json'

if FEED_CONFIG == 'DSX':
    DSX_FEED_CONTAINER = 'OSProject'
    DSX_AUTH_URL = "https://identity.open.softlayer.com/v3/auth/tokens"
    DSX_CREDENTIALS = {
        "region": "",
        "username": "",
        "password": "",
        "domainId": ""
    }
    FEED_URI = 'dsx://' + DSX_FEED_CONTAINER + '/%(name)s - %(time)s.json'

else:
    # By default, log the results in a local folder
    FEED_URI = './results/%(name)s.json'

# Lists to look for (case insensitive)
SECTIONS_KEYWORDS_FILE = './section_keywords.txt'

# Keywords to look for (case insensitive)
KEYWORDS_FILE = './keywords.txt'
