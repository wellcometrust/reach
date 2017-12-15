import scrapy
import os
import sys
from scrapy.http import Request
from tools.cleaners import clean_html
from wsf_scraping.items import WHOArticle
from pdf_parser.pdf_parse import (get_pdf_document, parse_pdf_document,
                                  grab_section)


class WhoIrisSpider(scrapy.Spider):
    name = 'who_iris'
    # All these parameters are optionnal,
    # but it is good to set a result per page ubove 250, to limit query number
    data = {
        'location': '',
        'query': '',
        'sort_by': 'score',
        'order': 'desc',
        'filter_field_1': 'dateIssued',
        'filter_type_1': 'equals',
        'order': 'desc',
    }

    def start_requests(self):
        # Set up per page results
        self.data['rpp'] = self.settings['WHO_IRIS_RPP']
        years = self.settings['WHO_IRIS_YEARS']
        urls = []
        # Initial URL (splited for PEP8 compliance)
        base_url = 'http://apps.who.int/iris/simple-search'
        url = base_url + '?location={location}&query={query}&rpp={rpp}'
        url += '&sort_by={sort_by}&order={order}'
        url += '&filter_field_1={filter_field_1}&filter_type_1={filter_type_1}'
        url += '&filter_value_1={filter_value_1}&filter_field_2=language'
        url += '&filter_type_2=equals&filter_value_2=en'

        for year in years:
            self.data['filter_value_1'] = year
            # Format it with initial data and launch the process
            urls.append((url.format(**self.data), year))

        for url in urls:
            print(url[0])
            yield scrapy.Request(
                url=url[0],
                callback=self.parse,
                meta={'year': url[1]}
            )

    def parse(self, response):
        """ Parse the articles listing page and go to the next one.

        @url http://apps.who.int/iris/simple-search?rpp=3
        @returns items 0 0
        @returns requests 4 4
        """

        year = response.meta.get('year', {})
        for href in response.css('.list-group-item::attr(href)').extract():
            yield Request(
                url=response.urljoin(href),
                callback=self.parse_article,
                meta={'year': year}
            )

        # Follow next link
        next_page = response.xpath(
            './/a[contains(., "next")]/@href'
        ).extract_first()
        yield Request(
            url=response.urljoin(next_page),
            callback=self.parse,
            meta={'year': year}
        )

    def parse_article(self, response):
        """ Scrape the article metadata from the detailed article page. Then,
        redirect to the PDF page.

        @url http://apps.who.int/iris/handle/10665/123400
        @returns requests 1 1
        @returns items 0 0
        """

        year = response.meta.get('year', {})
        data_dict = {
            'Year': year,
        }
        for tr in response.css('table.itemDisplayTable tr'):
            label = tr.css('td.metadataFieldLabel::text').extract_first()
            label = label[:label.find(':')]
            value = clean_html(tr.css('td.metadataFieldValue').extract_first())

            data_dict[label] = value

        # Scrap all the pdf on the page, passing scrapped metadata
        href = response.css('a[href$=".pdf"]::attr(href)').extract_first()
        yield Request(
            url=response.urljoin(href),
            callback=self.save_pdf,
            meta={'data_dict': data_dict}
        )

    def save_pdf(self, response):
        """ Retrieve the pdf file and scan it to scrape keywords and sections.

        @url http://apps.who.int/iris/bitstream/10665/123575/1/em_rc8_5_en.pdf
        @returns items 1 1
        @returns requests 0 0
        """

        # Retrieve metadata
        data_dict = response.meta.get('data_dict', {})
        section = ''

        # Populate a WHOArticle Item
        who_article = WHOArticle({
                'title': data_dict.get('Title', ''),
                'uri': data_dict.get('URI', ''),
                'year': data_dict.get('Year', ''),
                'authors': data_dict.get('Authors', ''),
                'sections': {},
                'keywords': {}
            }
        )
        # Download PDF file to /tmp
        filename = response.url.split('/')[-1]
        with open('/tmp/' + filename, 'wb') as f:
            f.write(response.body)

        # Convert PDF content to text format
        f = open('/tmp/' + filename, 'rb')
        document = get_pdf_document(f)
        pdf_file = parse_pdf_document(document)

        data_dict['Pdf'] = filename
        for keyword in self.settings['SEARCH_FOR_LISTS']:
            # Fetch references or other keyworded list
            section = grab_section(pdf_file, keyword)

            # Add references and PDF name to JSON returned file
            # If no section matchs, leave the attribute undefined
            if section:
                who_article['sections'][keyword.title()] = section

        for keyword in self.settings['SEARCH_FOR_KEYWORDS']:
            # Fetch references or other keyworded list
            section = pdf_file.get_lines_by_keyword(keyword)

            # Add references and PDF name to JSON returned file
            # If no section matchs, leave the attribute undefined
            if section:
                data_dict['keywords'][keyword.title()] = section

        # Remove the PDF file
        f.close()
        os.remove('/tmp/' + filename)
        return who_article
