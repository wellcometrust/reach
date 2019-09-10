from urllib.parse import urlencode

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
        url = 'https://www.gov.uk/search/policy-papers-and-consultations'

        query_dict = {
            'order': 'updated-newest',
            'content_store_document_type[]': 'policy_papers',
        }
        query_params = urlencode(query_dict)
        url = url + '?' + query_params

        self.logger.info('Initial url: %s', url)
        yield Request(
            url=url,
            dont_filter=True,
            callback=self.parse,
            errback=self.on_error,
        )

    def parse(self, response):
        """ Parse the articles listing page and go to the next one."""

        page_links = response.css(
            '.gem-c-document-list__item-title::attr("href")'
        ).extract()

        for href in page_links:
            yield Request(
                url=response.urljoin(href),
                callback=self.parse_article,
                errback=self.on_error,
            )

        next_page = response.css(
            '.gem-c-pagination__item--next a::attr("href")'
        ).extract_first()
        if next_page:
            yield Request(
                url=response.urljoin(next_page),
                callback=self.parse,
                errback=self.on_error,
            )

    def parse_article(self, response):
        """Parse the PDF files found in a gov_uk page. """

        document_links = response.css(
            '.attachment-details h2 a::attr("href")'
        ).extract()

        for fhref in document_links:
            title = response.css('h1::text').extract_first().strip('\n ')
            yield Request(
                url=response.urljoin(fhref),
                callback=self.save_pdf,
                errback=self.on_error,
                meta={'title': title}
            )


