from urllib.parse import urlencode
import os.path

from scrapy.http import Request
import scrapy

from .base_spider import BaseSpider


class GovSpider(BaseSpider):
    name = 'gov_uk'
    custom_settings = {
        'JOBDIR': BaseSpider.jobdir(name)
    }

    def __init__(self, **kwargs):
        """Initialise the class attribute year_before and year_after. The
        attribute year_before excludes everything from said year.
        e.g. 2013 and 2015 -> 01/01/2013 to 31/12/2014
        """
        year_before = kwargs.get('year_before', False)
        year_after = kwargs.get('year_after', False)
        id = kwargs.get('uuid', '')

        self.uuid = id
        self.year_before = year_before if year_before else ''
        self.year_after = year_after if year_after else ''

    def start_requests(self):
        """Sets up the base urls and start the initial requests."""
        url = 'https://www.gov.uk/government/publications'

        if self.year_before or self.year_after:
            query_dict = {
                'keywords': '',
                'publication_filter_option': 'all',
                'topics[]': 'all',
                'departments[]': 'all',
                'official_document_status': 'all',
                'world_locations[]': 'all',
                'from_date': '01/01/{}'.format(self.year_after),
                'to_date': '31/12/{}'.format(int(self.year_before) - 1)
            }
            query_params = urlencode(query_dict)
            url = url + '?' + query_params

        self.logger.info('Initial url: %s', url)
        yield scrapy.Request(
            url=url,
            callback=self.parse,
            errback=self.on_error,
            dont_filter=True,
        )

    def parse(self, response):
        """ Parse the articles listing page and go to the next one."""

        file_links = response.css(
            '.attachment-details .title a::attr("href")'
        ).extract()
        other_document_links = response.css(
            'li.document-row a::attr("href")'
        ).extract()

        for href in other_document_links:
            yield Request(
                url=response.urljoin(href),
                callback=self.parse,
                errback=self.on_error,
            )

        for fhref in file_links:
            title = response.css('h1::text').extract_first().strip('\n ')
            yield Request(
                url=response.urljoin(fhref),
                callback=self.save_pdf,
                errback=self.on_error,
                meta={'title': title}
            )

        next_page = response.css(
            'li.next a::attr("href")'
        ).extract_first()
        if next_page:
            yield Request(
                url=response.urljoin(next_page),
                callback=self.parse,
                errback=self.on_error,
            )
