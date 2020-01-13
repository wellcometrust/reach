import scrapy
from scrapy.http import Request
from .base_spider import BaseSpider


class UnicefSpider(BaseSpider):
    name = 'unicef'

    custom_settings = {
        'JOBDIR': BaseSpider.jobdir(name)
    }

    def start_requests(self):
        """ This sets up the urls to scrape for each years.
        """

        urls = [
            'https://data.unicef.org/resources/resource-type/publications/',
            'https://data.unicef.org/resources/resource-type/guidance/'
        ]

        for url in urls:
            self.logger.info('Initial url: %s', url)
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                errback=self.on_error,
                dont_filter=True,
            )

    def parse(self, response):
        """ Parse the articles listing page and go to the next one.

        @url https://data.unicef.org/resources/resource-type/publications/
        @returns items 0 0
        @returns requests 1
        """

        for href in response.css('h3 a::attr(href)').extract():
            yield Request(
                url=response.urljoin(href),
                callback=self.parse_article,
                errback=self.on_error,
            )

    def parse_article(self, response):
        """ Scrape the article metadata from the detailed article page. Then,
        redirect to the PDF page.

        @url https://data.unicef.org/resources/child-protection-resource-pack/
        @returns requests 1 1
        @returns items 0 0
        """

        title = response.css('h1::text').extract_first()
        hrefs = response.css('a::attr("href")').extract()
        ls = list(filter(lambda x: self._is_valid_pdf_url(x), hrefs))

        # Extract headings level 1 to 3 from the page
        headings = response.xpath("/html/body//*[self::h1 or self::h2 or self::h3]/text()")
        headings = [x.extract() for x in headings]

        for link in ls:
            data_dict = {
                'source_page': response.url,
                'page_title': response.xpath('/html/head/title/text()').extract_first(),
                'link_text': title,
                'title': title,
                'page_headings': headings
            }
            yield Request(
                url=response.urljoin(link),
                callback=self.save_pdf,
                errback=self.on_error,
                dont_filter=True,
                meta={'data_dict': data_dict}
            )
