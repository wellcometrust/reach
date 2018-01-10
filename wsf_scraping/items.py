# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class WHOArticle(scrapy.Item):
    title = scrapy.Field()
    uri = scrapy.Field()
    year = scrapy.Field()
    pdf = scrapy.Field()
    authors = scrapy.Field()
    sections = scrapy.Field()
    keywords = scrapy.Field()
