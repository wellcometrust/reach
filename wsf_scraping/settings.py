# -*- coding: utf-8 -*-
import datetime
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
# LOG_ENABLED = False
LOG_LEVEL = 'INFO'

# Force UTF-8 encoding
FEED_EXPORT_ENCODING = 'utf-8'

# Crawl responsibly by identifying yourself (and your website)
# USER_AGENT = 'wsf_scraping (+wateystrdjytkfu)'

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 64
CONCURRENT_REQUESTS_PER_DOMAIN = 64
RETRY_ENABLED = False
DOWNLOAD_WARNSIZE = 0
DOWNLOAD_TIMEOUT = 360

# Disable cookies (enabled by default)
COOKIES_ENABLED = False

#  who_iris and who_iris_single_page per-page results
WHO_IRIS_RPP = 250
WHO_IRIS_YEARS = [2012, 2013, 2014, 2015, 2016, 2017]

DUPEFILTER_CLASS = "wsf_scraping.filter.BLOOMDupeFilter"

FEED_FORMAT = 'jsonlines'
FEED_EXPORT_ENCODING = 'utf-8'

FEED_CONFIG = 'PROD'

if FEED_CONFIG == 'DEBUG':
    FEED_URI = './results/who_{date}.json'.format(date=datetime.datetime.now())
else:
    AWS_ACCESS_KEY_ID = "your_aws_id"
    AWS_SECRET_ACCESS_KEY = "your_aws_secret"
    FEED_URI = 's3://______your_s3_folder_name______/who_{date}.json'.format(
        date=datetime.datetime.now()
    )

# Lists to look for (case insensitive)
SEARCH_FOR_LISTS = ['references', 'bibliography', 'citations']

# Keywords to look for (case insensitive)
SEARCH_FOR_KEYWORDS = ['wellcome']
