# -*- coding: utf-8 -*-
import scrapy


class Article(scrapy.Item):
    def __repr__(self):
        return repr({
            'title': self.get('title'),
            'uri': self.get('uri'),
            'provider': self.get('provider'),
        })

    title = scrapy.Field()
    year = scrapy.Field()
    uri = scrapy.Field()
    pdf = scrapy.Field()
    sections = scrapy.Field()
    keywords = scrapy.Field()
    hash = scrapy.Field()
    text = scrapy.Field()
    types = scrapy.Field()
    subjects = scrapy.Field()
    authors = scrapy.Field()
    types = scrapy.Field()
    provider = scrapy.Field()
    date_scraped = scrapy.Field()
