import unittest
from scrapy.http import Response, Request
from wsf_scraping.spiders.base_spider import BaseSpider
from wsf_scraping.spiders.unicef_spider import UnicefSpider
from wsf_scraping.spiders.msf_spider import MSFSpider
from wsf_scraping.spiders.gov_spider import GovSpider
from wsf_scraping.spiders.parliament_spider import ParliamentSpider

TEST_PDF = 'tests/pdfs/test_pdf.pdf'


class TestSpiders(unittest.TestCase):

    def setUp(self):
        self.test_file = open(TEST_PDF, 'rb')

        meta = {
            'data_dict': {
                'title': 'foo',
            }
        }
        headers = {
            'content-type': b'application/pdf'
        }
        request = Request('http://foo.bar', meta=meta)
        self.pdf_response = Response(
            'http://foo.bar',
            body=self.test_file.read(),
            request=request,
            headers=headers
        )

    def tearDown(self):
        self.test_file.close()

    def test_base_spider(self):
        """Tests if, given a pdf-like response containing a data_dict metadata,
        the save_pdf method does:
          - Create a NamedTemporaryFile
          - Return an item
        """
        base_spider = BaseSpider()

        res = base_spider.save_pdf(self.pdf_response)
        self.assertTrue(res)
        self.assertTrue('foo' == res['title'])

    def test_unicef_spider(self):
        """Tests if, given a pdf-like response containing a data_dict metadata,
        the save_pdf method does:
          - Create a NamedTemporaryFile
          - Return an item
        """
        unicef_spider = UnicefSpider()

        res = unicef_spider.save_pdf(self.pdf_response)
        self.assertTrue(res)
        self.assertTrue('foo' == res['title'])

    def test_msf_spider(self):
        """Tests if, given a pdf-like response containing a data_dict metadata,
        the save_pdf method does:
          - Create a NamedTemporaryFile
          - Return an item
        """
        msf_spider = MSFSpider()

        res = msf_spider.save_pdf(self.pdf_response)
        self.assertTrue(res)
        self.assertTrue('foo' == res['title'])

    def test_gov_spider(self):
        """Tests if, given a pdf-like response containing a data_dict metadata,
        the save_pdf method does:
          - Create a NamedTemporaryFile
          - Return an item
        """
        gov_spider = GovSpider()

        res = gov_spider.save_pdf(self.pdf_response)
        self.assertTrue(res)
        self.assertTrue('foo' == res['title'])

    def test_parliament_spider(self):
        """Tests if, given a pdf-like response containing a data_dict metadata,
        the save_pdf method does:
          - Create a NamedTemporaryFile
          - Return an item
        """
        parliament_spider = ParliamentSpider()

        res = parliament_spider.save_pdf(self.pdf_response)
        self.assertTrue(res)
        self.assertTrue('foo' == res['title'])
