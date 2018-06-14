import json
import scrapy
from lxml import html
from scrapy.http import Request
from .base_spider import BaseSpider
from wsf_scraping.items import NICEArticle


class NiceSpider(BaseSpider):
    name = 'nice'

    custom_settings = {
        'JOBDIR': 'crawls/nice'
    }

    def start_requests(self):
        """Set up the initial request to the website to scrape."""

        articles_count = self.settings['NICE_ARTICLES_COUNT']

        # Initial URL (splited for PEP8 compliance). -1 length displays
        # the whole list.
        base_url = 'https://www.nice.org.uk/guidance/published/ajax'
        param1 = '?iDisplayLength=%s' % articles_count
        param2 = '&type=apg,csg,cg,mpg,ph,sg,sc'
        url = ''.join([base_url, param1, param2])

        # NICE guidance listing should be called by an AJAX requests
        headers = {
            'X-Requested-With': 'XMLHttpRequest',
            'referer': 'https://www.nice.org.uk/guidance/published'
        }

        self.logger.info('Initial url: %s', url)
        yield scrapy.Request(
            url=url,
            headers=headers,
            errback=self.on_error,
            dont_filter=True,
            callback=self.parse,
        )

    def parse(self, response):
        """ Parse the guidance listing page. Request must be done in AJAX,
        else the NICE website only send the default number of results (10).

        @ajax
        @url https://www.nice.org.uk/guidance/published/ajax?iDisplayLength=10
        @returns items 0 0
        @returns requests 10 30
        """

        # Grab the link to the detailed article, its evidences and history
        try:
            articles = json.loads(response.text)
            doc_links = []
            evidence_links = []
            history_links = []

            for doc in articles['aaData']:
                doc_link = html.fromstring(doc['ProductTitle']).get('href')

                doc_links.append('https://www.nice.org.uk%s' % doc_link)
                if self.settings.getbool('NICE_GET_EVIDENCES'):
                    evidence_links.append(
                        'https://www.nice.org.uk%s/evidence' % doc_link
                    )
                if self.settings.getbool('NICE_GET_HISTORY'):
                    history_links.append(
                        'https://www.nice.org.uk%s/history' % doc_link
                    )

            for url in doc_links:
                yield scrapy.Request(
                    url=url,
                    errback=self.on_error,
                    callback=self.parse_article
                )

            for url in evidence_links:
                yield scrapy.Request(
                    url=url,
                    errback=self.on_error,
                    callback=self.parse_related_documents
                )

            for url in history_links:
                yield scrapy.Request(
                    url=url,
                    errback=self.on_error,
                    callback=self.parse_related_documents
                )

        except json.decoder.JSONDecodeError:
            self.logger.info('Response was not json serialisable')
            return

    def parse_related_documents(self, response):
        """ Scrape the guidance evidencies. Then, redirect to the PDF pages.

        @url https://www.nice.org.uk/guidance/ta494/evidence
        @returns requests 1 1
        @returns items 0 0
        """

        data_dict = {
            'title': response.css('h1::text').extract_first(),
            'year': response.css(
                '.published-date time::attr(datetime)'
            ).extract_first()[:4]
        }
        # Scrap all the pdf on the page, passing scrapped metadata
        for href in response.css('.track-link::attr(href)').extract():
            yield Request(
                url=response.urljoin(href),
                errback=self.on_error,
                callback=self.save_pdf,
                meta={'data_dict': data_dict}
            )

    def parse_article(self, response):
        """ Scrape the guidance metadata from the detailed article page. Then,
        redirect to the PDF page.

        @url https://www.nice.org.uk/guidance/ta494
        @returns requests 1 1
        @returns items 0 0
        """

        data_dict = {
            'title': response.css('h1::text').extract_first(),
            'year': response.css(
                '.published-date time::attr(datetime)'
            ).extract_first()[:4]
        }

        # First case: PDF exists as PDF, epub etc.
        href = response.xpath(
            './/a[contains(., "Save as PDF")]/@href'
        ).extract_first()

        if not href:
            # Second case: PDF is a single footer download link
            href = response.css('.track-link::attr("href")').extract_first()

        if not href:
            # Third case: Direct download link, without menu
            href = response.css('#nice-download::attr("href")').extract_first()

        if href:
            return Request(
                url=response.urljoin(href),
                errback=self.on_error,
                callback=self.save_pdf,
                meta={'data_dict': data_dict}
            )

        else:
            self.logger.info(
                'No link found to download the pdf version (%s)',
                response.request.url
            )

    def save_pdf(self, response):
        """ Retrieve the pdf file and scan it to scrape keywords and sections.

        @url http://apps.who.int/iris/bitstream/10665/123575/1/em_rc8_5_en.pdf
        @returns items 0
        @returns requests 0 0
        """

        data_dict = response.meta.get('data_dict', {})

        is_pdf = self._check_headers(response.headers)

        if not is_pdf:
            self.logger.info('Not a PDF, aborting (%s)', response.url)
            return

        filename = ''.join([response.url.split('/')[-1], '.pdf'])

        with open('/tmp/' + filename, 'wb') as f:
            f.write(response.body)

        nice_article = NICEArticle({
                'title': data_dict.get('title', ''),
                'uri': response.request.url,
                'year': data_dict.get('year', ''),
                'pdf': filename,
                'sections': {},
                'keywords': {}
        })

        yield nice_article
