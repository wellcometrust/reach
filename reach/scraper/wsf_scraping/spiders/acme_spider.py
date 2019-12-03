import scrapy
from urllib.parse import urlencode
from scrapy.http import Request
from collections import defaultdict
from .base_spider import BaseSpider


class AcmeSpider(BaseSpider):
    name = 'acme'
    data = {}

    custom_settings = {
        'JOBDIR': BaseSpider.jobdir(name)
    }

    def start_requests(self):
        """ This sets up the urls to scrape for each years.
        """
        keys = [key for key in self.settings.keys()]
        urls = ['http://scrape-target:8888']
        # Initial URL (splited for PEP8 compliance)

        for url in urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                errback=self.on_error,
                dont_filter=True,
                meta={'year': 2018}
            )

    def parse(self, response):
        """ Parse the articles listing page and go to the next one.

        @url http://apps.who.int/iris/discover?rpp=3
        @returns items 0 0
        @returns requests 3 4
        """

        year = response.meta.get('year', {})
        for href in response.css('.doc-page-link::attr("href")').extract():
            yield Request(
                url=response.urljoin(href),
                callback=self.parse_article,
                errback=self.on_error,
                dont_filter=True,
                meta={'year': year}
            )

    def parse_article(self, response):
        """ Scrape the article metadata from the detailed article page. Then,
        redirect to the PDF page.

        @url http://apps.who.int/iris/handle/10665/272346?show=full
        @returns requests 1 1
        @returns items 0 0
        """

        # Scrap all the pdf on the page, passing scrapped metadata
        href = response.css(
            '.doc-download-link::attr("href")'
        ).extract_first()

        data_dict = {
            'source_page': response.url,
            'page_title': response.xpath('//title/text()').extract_first(),
        }

        if self._is_valid_pdf_url(href):
            yield Request(
                url=response.urljoin(href),
                callback=self.save_pdf,
                errback=self.on_error,
                dont_filter=True,
                meta={'data_dict': data_dict}
            )
        else:
            err_link = href if href else ''.join([response.url, ' (referer)'])
            self.logger.debug(
                "Item is null - Canceling (%s)",
                err_link
            )
