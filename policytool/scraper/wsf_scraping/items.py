# -*- coding: utf-8 -*-
import scrapy


class Article(scrapy.Item):
    def __repr__(self):
        return repr({
            'title': self.get('title'),
            'uri': self.get('uri'),
        })

    title = scrapy.Field()
    year = scrapy.Field()
    uri = scrapy.Field()
    pdf = scrapy.Field()
    hash = scrapy.Field()
    has_text = scrapy.Field()
    types = scrapy.Field()
    subjects = scrapy.Field()
    authors = scrapy.Field()
    types = scrapy.Field()
    date_scraped = scrapy.Field()
