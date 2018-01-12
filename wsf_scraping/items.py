# -*- coding: utf-8 -*-

import scrapy


class WHOArticle(scrapy.Item):
    title = scrapy.Field()
    uri = scrapy.Field()
    year = scrapy.Field()
    pdf = scrapy.Field()
    authors = scrapy.Field()
    sections = scrapy.Field()
    keywords = scrapy.Field()
