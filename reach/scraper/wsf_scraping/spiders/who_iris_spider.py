import scrapy
from urllib.parse import urlencode
from scrapy.http import Request
from collections import defaultdict
from .base_spider import BaseSpider


class WhoIrisSpider(BaseSpider):
    name = 'who_iris'
    data = {}

    custom_settings = {
        'JOBDIR': BaseSpider.jobdir(name)
    }

    def start_requests(self):
        """ This sets up the urls to scrape for each years.
        """
        keys = [key for key in self.settings.keys()]
        years = self.settings['WHO_IRIS_YEARS']
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

        for year in years:
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

        data_dict = dict()
        data_dict['year'] = response.meta.get('year', {})
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

        # Extract headings level 1 to 3 from the page
        headings = response.xpath("/html/body//*[self::h1 or self::h2 or self::h3]/text()")
        headings = [x.extract() for x in headings]

        if self._is_valid_pdf_url(href):
            data_dict['source_page'] = response.url
            data_dict['page_title'] = response.xpath('/html/head/title/text()').extract_first()
            data_dict['link_text'] = None
            data_dict['page_headings'] = headings
            yield Request(
                url=response.urljoin(href),
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
