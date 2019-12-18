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

        items = map(result_mapper, response.css(".doc-download-link"))

        # Extract headings level 1 to 3 from the page
        headings = response.xpath("/html/body//*[self::h1 or self::h2 or self::h3]/text()")
        headings = [x.extract() for x in headings]

        data_dict = {
            'source_page': response.url,
            'page_title': response.xpath('/html/head/title/text()').extract_first(),
            'page_headings': headings
        }

        for item in items:
            if self._is_valid_pdf_url(item[0]):
                data_dict['filename'] = item[0].split("/")[-1] or None
                data_dict['link_text'] = item[1]
                yield Request(
                    url=response.urljoin(item[0]),
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

def result_mapper(item):
    return (
        item.attrib['href'],
        item.xpath('text()').extract_first(),
    )
