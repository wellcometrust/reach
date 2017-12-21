# -*- coding: utf-8 -*-
import datetime
import logging

# Scrapy settings for wsf_scraping project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#     http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
#     http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html


BOT_NAME = 'wsf_scraper'

SPIDER_MODULES = ['wsf_scraping.spiders']
NEWSPIDER_MODULE = 'wsf_scraping.spiders'

# Logging settings: Log all into a file, basic level is INFO.
LOG_LEVEL = 'INFO'
LOG_FILE = 'var/log-{log_level}.txt'.format(log_level=LOG_LEVEL)
LOG_SDTOUT = True
LOG_ENABLED = True
# Set pdfminer log to WARNING, should stay that way as pdfminer echoes a lot
# of unuseful log.
logging.getLogger("pdfminer").setLevel(logging.WARNING)

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 64
CONCURRENT_REQUESTS_PER_DOMAIN = 64
RETRY_ENABLED = False
DOWNLOAD_WARNSIZE = 0
DOWNLOAD_TIMEOUT = 360

# Use a physical queue, slower but add fiability
SCHEDULER_MEMORY_QUEUE = 'scrapy.squeues.FifoMemoryQueue'
DUPEFILTER_CLASS = "wsf_scraping.filter.BLOOMDupeFilter"

# Autothrottle for best performances, and to be more respectful of the website
# we are scraping.
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 0.1
AUTOTHROTTLE_MAX_DELAY = 0.5
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0

# Disable cookies
COOKIES_ENABLED = False

#  who_iris and who_iris_single_page dedicated settings
WHO_IRIS_RPP = 250
WHO_IRIS_YEARS = [2012, 2013, 2014, 2015, 2016, 2017]

# Jsonlines are cleaner for big feeds
FEED_FORMAT = 'jsonlines'
FEED_EXPORT_ENCODING = 'utf-8'
FEED_TEMPDIR = 'var/tmp/'

# Prod feed export to amazon s3
FEED_CONFIG = 'DEBUG'

if FEED_CONFIG == 'S3':
    AWS_ACCESS_KEY_ID = "______your_aws_id______"
    AWS_SECRET_ACCESS_KEY = "______your_aws_secret______"
    FEED_URI = 's3://__your_s3_bucket__/scraping/feeds/%(name)s/%(time)s.json'
else:
    FEED_URI = './results/who_{date}.json'.format(date=datetime.datetime.now())

# Lists to look for (case insensitive)
SEARCH_FOR_LISTS = ['reference', 'bibliography', 'citation']

# Keywords to look for (case insensitive)
SEARCH_FOR_KEYWORDS = ['wellcome']
