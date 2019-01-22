import scrapy
from .base_spider import BaseSpider


class MSFSpider(BaseSpider):
    name = 'msf'

    custom_settings = {
        'JOBDIR': 'crawls/msf'
    }

    def start_requests(self):
        """Set up the initial request to the website to scrape."""

        urls = [
            'https://www.msf.org.uk/activity-reports',
            'https://www.msf.org.uk/reports',
        ]

        for url in urls:
            self.logger.info('Initial url: %s', url)
            yield scrapy.Request(
                url=url,
                errback=self.on_error,
                dont_filter=True,
                callback=self.parse,
            )

    def parse(self, response):
        """ Parse both reports and activity-reports pages.

        @url https://www.msf.org.uk/activity-reports
        @returns items 0 0
        @returns requests 10
        """

        doc_links = response.css('.field-items a::attr(href)').extract()
        for url in doc_links:
            yield scrapy.Request(
                url=response.urljoin(url),
                errback=self.on_error,
                callback=self.save_pdf
            )
