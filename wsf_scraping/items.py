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
    types = scrapy.Field()
    subjects = scrapy.Field()


class NICEArticle(scrapy.Item):
    title = scrapy.Field()
    uri = scrapy.Field()
    year = scrapy.Field()
    pdf = scrapy.Field()
    sections = scrapy.Field()
    keywords = scrapy.Field()


class UNICEFArticle(scrapy.Item):
    title = scrapy.Field()
    uri = scrapy.Field()
    pdf = scrapy.Field()
    sections = scrapy.Field()
    keywords = scrapy.Field()
