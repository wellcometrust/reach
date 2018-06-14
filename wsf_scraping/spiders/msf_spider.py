import scrapy
from .base_spider import BaseSpider
from wsf_scraping.items import MSFArticle


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

    def save_pdf(self, response):
        """ Retrieve the pdf file and scan it to scrape keywords and sections.
        """

        is_pdf = self._check_headers(response.headers)

        if not is_pdf:
            self.logger.info('Not a PDF, aborting (%s)', response.url)
            return

        filename = ''.join([response.url.split('/')[-1], '.pdf'])

        with open('/tmp/' + filename, 'wb') as f:
            f.write(response.body)

        msf_article = MSFArticle({
                'title': '',
                'uri': response.request.url,
                'pdf': filename,
                'sections': {},
                'keywords': {}
        })

        yield msf_article
