# -*- coding: utf-8 -*-
import scrapy


class BaseArticle(scrapy.Item):
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
    provider = scrapy.Field()
    date_scraped = scrapy.Field()


class WHOArticle(BaseArticle):
    types = scrapy.Field()
    subjects = scrapy.Field()
    authors = scrapy.Field()


class NICEArticle(BaseArticle):
    pass


class UNICEFArticle(BaseArticle):
    pass


class MSFArticle(BaseArticle):
    pass


class GovArticle(BaseArticle):
    pass
