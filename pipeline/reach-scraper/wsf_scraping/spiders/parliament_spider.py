import scrapy
from scrapy.http import Request
from .base_spider import BaseSpider


class ParliamentSpider(BaseSpider):
    name = 'parliament'

    custom_settings = {
        'ROBOTSTXT_OBEY': False
    }

    def start_requests(self):
        """This sets up the initial urls."""

        query_list = [
            "Parameters.Fields.all=",
            "Parameters.Fields.all-target=",
            "Parameters.Fields.phrase=",
            "Parameters.Fields.phrase-target=",
            "Parameters.Fields.any=",
            "Parameters.Fields.any-target=",
            "Parameters.Fields.exclude=",
            "Parameters.Fields.exclude-target=",
            "Parameters.Fields.type=Bills",
            "Parameters.Fields.type=Select+Committee+reports",
            "Parameters.Fields.type=Select+Committee+written+evidence",
            "Parameters.Fields.type=Debates",
            "Parameters.Fields.type=Research+briefings",
            "Parameters.Fields.member=",
            "Parameters.Fields.subject=",
            "Parameters.Fields.reference=",
            "When%3A=date",
            "Parameters.Fields.date=01%2F01%2F1980",
            "Parameters.Fields.date=04%2F10%2F2018",
            "Parameters.PageSize=100"
        ]
        base_url = 'http://search-material.parliament.uk/search'
        query_params = '&'.join(query_list)
        url = base_url + '?' + query_params

        self.logger.info('Initial url: %s', url)
        yield scrapy.Request(
            url=url,
            callback=self.parse,
            errback=self.on_error,
        )

    def parse(self, response):
        """Parse the articles listing page and go to the next one."""

        for li in response.css('#results li'):
            # direct pdfs links ends with pdf
            link = li.css('h4 a::attr(href)').extract_first().strip()
            meta = li.css('.resultdetails::text').extract()
            meta = [m.strip() for m in meta]

            # The date is always in format `dd Mmm YYYY`
            title = li.css('h4 a::text').extract_first().strip()
            year = meta[0][-4:]
            types = meta[1]

            # Extract headings level 1 to 3 from the page
            headings = response.xpath("/html/body//*[self::h1 or self::h2 or self::h3]/text()")
            headings = [x.extract() for x in headings]

            data_dict = {
                'source_page': response.url,
                'page_title': response.xpath('/html/head/title/text()').extract_first(),
                'link_text': title,
                'title': title,
                'year': year,
                'types': types,
                'page_headings': headings
            }

            yield Request(
                url=response.urljoin(link),
                meta=data_dict,
                callback=self.parse_others,
                errback=self.on_error,
            )

        next = response.css('.next a::attr(href)').extract_first()
        if next:
            yield Request(
                url=response.urljoin(next),
                callback=self.parse,
                errback=self.on_error,
            )

    def parse_others(self, response):
        """Try to retrieve a pdf from a depth 2 page. If no pdf is found
        at this point, we stop looking this way.
        """

        if self._is_valid_pdf(response):
            yield Request(
                url=response.urljoin(response.request.url),
                meta={'data_dict': response.meta},
                callback=self.save_pdf,
                errback=self.on_error,
            )
        elif self._check_headers(
            response.headers,
            b'text/html',
        ):
            for href in response.css('a::attr(href)').extract():
                url = response.urljoin(href)
                if self._is_valid_pdf_url(url):
                    yield Request(
                        url=url,
                        meta={'data_dict': response.meta},
                        callback=self.save_pdf,
                        dont_filter=True,
                        errback=self.on_error,
                    )

        yield
