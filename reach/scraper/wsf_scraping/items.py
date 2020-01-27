# -*- coding: utf-8 -*-
import scrapy


class Article(scrapy.Item):

    def __repr__(self):
        return repr({
            'title': self.get('title'),
            'url': self.get('url'),
        })

    title = scrapy.Field()
    year = scrapy.Field()
    url = scrapy.Field()
    url_filename = scrapy.Field()
    pdf = scrapy.Field()
    hash = scrapy.Field()
    has_text = scrapy.Field()
    types = scrapy.Field()
    subjects = scrapy.Field()
    authors = scrapy.Field()
    types = scrapy.Field()
    date_scraped = scrapy.Field()
    page_title = scrapy.Field()
    source_page = scrapy.Field()
    disposition_title = scrapy.Field()
    link_title = scrapy.Field()
    page_headings = scrapy.Field()
    path = scrapy.Field()
