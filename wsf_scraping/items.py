# -*- coding: utf-8 -*-
import scrapy


class BaseArticle(scrapy.Item):
    title = scrapy.Field()
    uri = scrapy.Field()
    pdf = scrapy.Field()
    sections = scrapy.Field()
    keywords = scrapy.Field()
    hash = scrapy.Field()
    text = scrapy.Field()
    provider = scrapy.Field()
    date_scraped = scrapy.Field()


class WHOArticle(BaseArticle):
    year = scrapy.Field()
    types = scrapy.Field()
    subjects = scrapy.Field()
    authors = scrapy.Field()


class NICEArticle(BaseArticle):
    year = scrapy.Field()


class UNICEFArticle(BaseArticle):
    pass


class MSFArticle(BaseArticle):
    pass


class GovArticle(BaseArticle):
    pass
