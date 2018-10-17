import scrapy
from scrapy.http import Request
from wsf_scraping.items import ParliamentArticle
from .base_spider import BaseSpider


class ParliamentSpider(BaseSpider):
    name = 'parliament'

    custom_settings = {
        'JOBDIR': 'crawls/parliament',
        'ROBOTSTXT_OBEY': False
    }

    def start_requests(self):
        """This sets up the initial urls."""

        query_list = [
            'Parameters.Fields.all=',
            'Parameters.Fields.all-target=',
            'Parameters.Fields.phrase=',
            'Parameters.Fields.phrase-target=',
            'Parameters.Fields.any=',
            'Parameters.Fields.any-target=',
            'Parameters.Fields.exclude=',
            'Parameters.Fields.exclude-target=',
            'Parameters.Fields.house=House+of+Commons',
            'Parameters.Fields.house=House+of+Lords',
            'Parameters.Fields.member=',
            'Parameters.Fields.subject=',
            'Parameters.Fields.reference=',
            'When%3A=date',
            'Parameters.Fields.date=01%2F01%2F1980',
            'Parameters.Fields.date=04%2F10%2F2018',
            'Parameters.PageSize=100'
        ]
        base_url = 'http://search-material.parliament.uk/search'
        query_params = '&'.join(query_list)
        url = base_url + '?' + query_params

        self.logger.info('Initial url: %s', url)
        yield scrapy.Request(
            url=url,
            callback=self.parse,
            errback=self.on_error,
            dont_filter=True,
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
            type = meta[1]

            yield Request(
                url=response.urljoin(link),
                meta={
                    'title': title,
                    'year': year,
                    'type': type
                },
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

        # Some of the parliament's pdf are categorised as octetstream
        is_pdf = self._check_headers(
            response.headers
        ) or self._check_headers(
            response.headers,
            b'application/octet-stream'
        )

        if is_pdf:
            yield Request(
                url=response.urljoin(response.request.url),
                meta={
                    'title': response.meta.get('title'),
                    'year': response.meta.get('year'),
                    'type': response.meta.get('type'),
                },
                callback=self.save_pdf,
                errback=self.on_error,
            )
        else:
            for href in response.css('a::attr(href)').extract():
                if href.endswith('pdf'):
                    yield Request(
                        url=response.urljoin(href),
                        meta={
                            'title': response.meta.get('title'),
                            'year': response.meta.get('year'),
                            'type': response.meta.get('type'),
                        },
                        callback=self.save_pdf,
                        errback=self.on_error,
                    )

    def save_pdf(self, response):
        """Retrieve the pdf file and scan it to scrape keywords and sections.
        """

        # Some of the parliament's pdf are categorised as octetstream
        is_pdf = self._check_headers(
            response.headers
        ) or self._check_headers(
            response.headers,
            b'application/octet-stream'
        )

        if not is_pdf:
            self.logger.info('Not a PDF, aborting (%s)', response.url)
            return

        # Download PDF file to /tmp
        filename = self._save_file(response.url, response.body)
        parliament_article = ParliamentArticle({
                'title': response.meta.get('title'),
                'year': response.meta.get('year'),
                'types': [response.meta.get('type')],
                'uri': response.request.url,
                'pdf': filename,
                'sections': {},
                'keywords': {}
            }
        )

        yield parliament_article
