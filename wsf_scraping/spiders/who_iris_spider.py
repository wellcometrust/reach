import scrapy
from urllib.parse import urlencode
from scrapy.http import Request
from collections import defaultdict
from wsf_scraping.items import WHOArticle
from .base_spider import BaseSpider


class WhoIrisSpider(BaseSpider):
    name = 'who_iris'
    data = {}

    custom_settings = {
        'JOBDIR': 'crawls/who_iris'
    }

    def start_requests(self):
        """ This sets up the urls to scrape for each years.
        """

        urls = []
        # Initial URL (splited for PEP8 compliance)
        query_dict = {
            'rpp': self.settings['WHO_IRIS_RPP'],
            'etal': 0,
            'group_by': 'none',
            'filtertype_0': 'dateIssued',
            'filtertype_1': 'iso',
            'filter_relational_operator_0': 'contains',
            'filter_relational_operator_1': 'contains',
            'filter_1': 'en',
        }
        base_url = 'http://apps.who.int/iris/discover'
        query_params = urlencode(query_dict) + '&filter_0={filter_0}'
        url = base_url + '?' + query_params

        for year in self.years:
            self.data['filter_0'] = year
            # Format it with initial data and launch the process
            urls.append((url.format(**self.data), year))

        for url in urls:
            self.logger.info('Initial url: %s', url[0])
            yield scrapy.Request(
                url=url[0],
                callback=self.parse,
                errback=self.on_error,
                dont_filter=True,
                meta={'year': url[1]}
            )

    def parse(self, response):
        """ Parse the articles listing page and go to the next one.

        @url http://apps.who.int/iris/discover?rpp=3
        @returns items 0 0
        @returns requests 3 4
        """

        year = response.meta.get('year', {})
        for href in response.css('.artifact-title a::attr(href)').extract():
            full_records_link = ''.join([href, '?show=full'])
            yield Request(
                url=response.urljoin(full_records_link),
                callback=self.parse_article,
                errback=self.on_error,
                meta={'year': year}
            )

        if not self.settings['WHO_IRIS_LIMIT']:
            # Follow next link if it exists and if we enabled it
            next_page = response.css(
                 '.next-page-link::attr("href")'
            ).extract_first()
            if next_page:
                yield Request(
                    url=response.urljoin(next_page),
                    callback=self.parse,
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

        data_dict = {
            'year': response.meta.get('year', {}),
        }
        data_dict['title'] = response.css(
            'h2.page-header::text'
        ).extract_first()

        details_dict = defaultdict(list)
        for line in response.css('.detailtable tr'):

            # Each tr should have 2 to 3 td: attribute, value and language.
            # We're only interested in the first and the second one.
            tds = line.css('td::text').extract()
            if len(tds) < 2:
                continue

            # Make attribute human readable
            # (first part is always 'dc', so skip it)
            attr_name = ' '.join(tds[0].split('.')[1:]).lower()
            details_dict[attr_name].append(f'{tds[1]}')

        # Scrap all the pdf on the page, passing scrapped metadata
        href = response.css(
            '.file-link a::attr("href")'
        ).extract_first()

        data_dict['subjects'] = set(details_dict.get('subject mesh', []))
        data_dict['types'] = set(details_dict.get('type', []))
        data_dict['authors'] = ', '.join(
            details_dict.get('contributor author', [])
        )
        if href:
            yield Request(
                url=response.urljoin(href),
                callback=self.save_pdf,
                errback=self.on_error,
                meta={'data_dict': data_dict}
            )
        else:
            err_link = href if href else ''.join([response.url, ' (referer)'])
            self.logger.debug(
                "Item is null - Canceling (%s)",
                err_link
            )

    def save_pdf(self, response):
        """ Retrieve the pdf file and scan it to scrape keywords and sections.

        @url http://apps.who.int/iris/bitstream/10665/123575/1/em_rc8_5_en.pdf
        @returns items 1 1
        @returns requests 0 0
        """

        is_pdf = self._check_headers(response.headers)

        if not is_pdf:
            self.logger.info('Not a PDF, aborting (%s)', response.url)
            return

        # Retrieve metadata
        data_dict = response.meta.get('data_dict', {})

        # Download PDF file to /tmp
        filename = self._save_file(response.url, response.body)
        who_article = WHOArticle({
                'title': data_dict.get('title', ''),
                'uri': response.request.url,
                'year': data_dict.get('year', ''),
                'authors': data_dict.get('authors', ''),
                'types': data_dict.get('types'),
                'subjects': data_dict.get('subjects'),
                'pdf': filename,
                'sections': {},
                'keywords': {}
            }
        )

        yield who_article
