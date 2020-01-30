import scrapy
from .base_spider import BaseSpider


class MsfSpider(BaseSpider):
    name = 'msf'


    def start_requests(self):
        """Set up the initial request to the website to scrape."""

        urls = [
            'https://www.msf.org.uk/activity-reports',
            'https://www.msf.org.uk/reports',
        ]

        for url in urls:
            callback = self.parse
            if "/reports" in url:
                callback = self.parse_reports

            self.logger.info('Initial url: %s', url)
            yield scrapy.Request(
                url=url,
                errback=self.on_error,
                callback=callback,
            )

    def parse(self, response):
        """ Parse activity-reports pages.

        @url https://www.msf.org.uk/activity-reports
        @returns items 0 0
        @returns requests 10
        """

        # TODO: Can pull document title from image alt or title properties

        doc_links = list(response.css('.field-item p'))


        for item in doc_links:
            url = item.xpath('.//a[@class="btn"]/@href').extract_first()
            image_alt = item.xpath('.//img[@class="media-element file-default"]/@alt').extract_first()

            if self._is_valid_pdf_url(url):
                data_dict = {
                    'source_page': response.url,
                    'page_title': response.xpath('/html/head/title/text()').extract_first(),
                    'title': image_alt
                }
                yield scrapy.Request(
                    url=response.urljoin(url),
                    errback=self.on_error,
                    callback=self.save_pdf,
                    meta={'data_dict': data_dict}
                )

    def parse_reports(self, response):
        """ Parse reports page

        Args:
            url: The reports page
        Returns:
            items
            requests
        """

        doc_links = list(response.css('.field-item a'))

        data_dict = {
            'source_page': response.url,
            'page_title': response.xpath('/html/head/title/text()').extract_first(),
            'title': None
        }

        for item in doc_links:
            url = item.xpath('@href').extract_first()
            if self._is_valid_pdf_url(url):
                data_dict['title'] = item.xpath('text()').extract_first()
                yield scrapy.Request(
                    url=response.urljoin(url),
                    errback=self.on_error,
                    callback=self.save_pdf,
                    dont_filter=True,
                    meta={'data_dict': data_dict}
                )



