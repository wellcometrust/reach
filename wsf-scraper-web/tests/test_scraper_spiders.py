import unittest
from scrapy.http import Response, Request
from wsf_scraping.spiders.base_spider import BaseSpider

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
