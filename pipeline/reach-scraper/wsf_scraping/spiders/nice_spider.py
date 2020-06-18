import scrapy
from scrapy.http import Request
from .base_spider import BaseSpider


class NiceSpider(BaseSpider):
    """ Handle crawling responses for the nice.org.uk web site

        Note: NICE may not return valid extension based URLs
            for actual PDF files, so this has to operate on
            content-type of a requests response in order to
            decide whether to save it.
    """

    name = 'nice'


    def start_requests(self):
        """Set up the initial request to the website to scrape."""

        # Initial URL (splited for PEP8 compliance). -1 length displays
        # the whole list.
        url = ('https://www.nice.org.uk/Search?'
               'om=[{%22gst%22:[%22Published%22]}]&ps=50&sp=on')

        self.logger.info('Initial url: %s', url)
        yield scrapy.Request(
            url=url,
            errback=self.on_error,
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
        articles = response.css(
            'h3.card__heading a::attr(href)'
        ).extract()
        doc_links = []
        evidence_links = []
        history_links = []

        for doc_link in articles:

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

        next_page_url = response.xpath(
            './/li/a[contains(., "Next")]/@href'
        ).extract_first()
        if next_page_url:
            yield Request(
                url=response.urljoin(next_page_url),
                callback=self.parse,
                errback=self.on_error,
                dont_filter=True,
            )

    def parse_related_documents(self, response):
        """ Scrape the guidance evidencies. Then, redirect to the PDF pages.

        @url https://www.nice.org.uk/guidance/ng2/evidence
        @returns requests 3
        @returns items 0 0
        """

        # Extract headings level 1 to 3 from the page
        headings = response.xpath("/html/body//*[self::h1 or self::h2 or self::h3]/text()")
        headings = [x.extract() for x in headings]

        title = response.css('h1::text').extract_first()
        year = response.css('.published-date time::attr(datetime)').extract_first()[:4]

        # Scrape all the pdf on the page, passing scraped metadata
        for href in response.css('.track-link::attr(href)').extract():
            if self._is_valid_pdf_url(href):
                data_dict = {
                    'source_page': response.url,
                    'page_title': response.xpath('/html/head/title/text()').extract_first(),
                    'link_text': None,
                    'page_headings': headings,
                    'title': title,
                    'year': year
                }
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

        date = response.css(
            '.published-date time::attr(datetime)'
        ).extract_first()

        title = response.css('h1::text').extract_first()
        year = date[:4] if date else None

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

        url = response.urljoin(href)
        if url:
            # Extract headings level 1 to 3 from the page
            headings = response.xpath("/html/body//*[self::h1 or self::h2 or self::h3]/text()")
            headings = [x.extract() for x in headings]

            # Nice doesn't supply file extensions for its downloads
            # so contrary to other spiders, we don't check for a valid
            # PDF URL here.
            # TODO: Maybe do an OPTION call to the route first to avoid
            # downloadning the whole page in case it's not a PDF, would
            # save some time, as some of these routes aren't PDFs (images, etc...)
            data_dict = {
                'source_page': response.url,
                'page_title': response.xpath('/html/head/title/text()').extract_first(),
                'title': title,
                'year': year,
                'link_text': None,
                'page_headings': headings
            }
            yield Request(
                url=url,
                errback=self.on_error,
                callback=self.save_pdf,
                dont_filter=True,
                meta={'data_dict': data_dict}
            )

        else:
            self.logger.info(
                'No link found to download the pdf version (%s)',
                response.request.url
            )
