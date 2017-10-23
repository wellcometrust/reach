import scrapy
import os
import re
from tools.extraction import convert, grab_references, cleanhtml
from scrapy.http import Request


class QuotesSpider(scrapy.Spider):
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
        'filter_value_1': 2012,
        'order': 'desc',
    }

    def start_requests(self):
        # Set up per page results
        data['rpp'] = self.settings['WHO_IRIS_RPP']

        # Initial URL (splited for PEP8 compliance)
        base_url = 'http://apps.who.int/iris/simple-search'
        url = base_url + '?location={location}&query={query}&rpp={rpp}'
        url += '&sort_by={sort_by}&order={order}'
        url += '&filter_field_1={filter_field_1}&filter_type_1={filter_type_1}'
        url += '&filter_value_1={filter_value_1}&filter_field_2=language'
        url += '&filter_type_2=equals&filter_value_2=en'

        # Format it with initial data and launch the process
        url = url.format(**self.data)
        print url
        yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        # Grab the link to the detailed article
        for href in response.css('.list-group-item::attr(href)').extract():
            yield Request(
                url=response.urljoin(href),
                callback=self.parse_article
            )

        # Follow next link
        next_page = response.xpath(
            './/a[contains(., "next")]/@href'
        ).extract_first()
        yield Request(
            url=response.urljoin(next_page),
        )

    def parse_article(self, response):

        # Scrap the article metadata
        data_dict = {}
        for tr in response.css('table.itemDisplayTable tr'):
            label = tr.css('td.metadataFieldLabel::text').extract_first()
            label = label[:label.find(':')]
            value = cleanhtml(tr.css('td.metadataFieldValue').extract_first())

            data_dict[label] = value

        # Scrap all the pdf on the page, passing scrapped metadata
        for href in response.css('a[href$=".pdf"]::attr(href)').extract():
            yield Request(
                url=response.urljoin(href),
                callback=self.save_pdf,
                meta={'data_dict': data_dict}
            )

    def save_pdf(self, response):
        # Retrieve metadata
        data_dict = response.meta.get('data_dict', {})

        # Download PDF file to /tmp
        filename = response.url.split('/')[-1]
        with open('/tmp/' + filename, 'wb') as f:
            f.write(response.body)

        # Convert PDF content to text format
        text_file = convert('/tmp/' + filename)

        # Fetch references
        refs = grab_references(text_file)

        # Add references and PDF name to JSON returned file
        data_dict['Pdf'] = filename
        data_dict['References'] = refs if refs else None

        # Remove the PDF file
        os.remove('/tmp/' + filename)

        yield data_dict
