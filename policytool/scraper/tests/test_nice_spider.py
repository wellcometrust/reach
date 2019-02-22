import unittest
from scrapy.http import Response, Request, HtmlResponse, TextResponse
from scrapy.utils.project import get_project_settings
from wsf_scraping.spiders.nice_spider import NiceSpider

TEST_PDF = 'tests/pdfs/test_pdf.pdf'


class Crawler:

    class Stats:
        def get_value(*args):
            return None

    stats = Stats()


class TestNiceSpider(unittest.TestCase):

    def setUp(self):
        self.test_file = open(TEST_PDF, 'rb')
        self.spider = NiceSpider()
        self.spider.settings = get_project_settings()
        self.spider.crawler = Crawler()

    def tearDown(self):
        self.test_file.close()

    def test_save_pdf(self):
        """Tests if, given a pdf-like response containing a data_dict metadata,
        the save_pdf method does:
          - Create a NamedTemporaryFile
          - Return an item
        """

        meta = {
            'data_dict': {
                'title': 'foo',
            }
        }

        headers = {
            'content-type': b'application/pdf'
        }

        request = Request('http://foo.bar', meta=meta)
        pdf_response = Response(
            'http://foo.bar',
            body=self.test_file.read(),
            request=request,
            headers=headers
        )

        res = self.spider.save_pdf(pdf_response)
        self.assertTrue(res)
        self.assertTrue('foo' == res['title'])

    def test_parse(self):
        """Test if given an publication listing page of the nice website,
        the spider yields a request to a publication, a request to
        its history and a request to its evidences.
        """

        with open('./tests/mock_sites/nice/1.html', 'r') as html_site:
            request = Request('http://foo.bar')
            response = TextResponse(
                'http://foo.bar',
                body=html_site.read(),
                request=request,
                encoding='utf-8'
            )

            res = self.spider.parse(response)

            # Check if the spider sends three requests to the other functions.
            self.assertTrue(next(res))
            self.assertTrue(next(res))

    def test_parse_article(self):
        """Test if given an publication listing page of the who website,
        the spider yields a request to a publication.
        """

        with open('./tests/mock_sites/nice/2.html', 'rb') as html_site:
            request = Request('http://foo.bar')
            response = HtmlResponse(
                'http://foo.bar',
                body=html_site.read(),
                request=request,
                encoding='utf-8'
            )

            res = next(self.spider.parse_article(response))

            self.assertTrue(res)
            self.assertTrue(res.meta.get('data_dict'))
            data_dict = res.meta['data_dict']
            self.assertEqual(data_dict['title'],
                             'StoneChecker for kidney stone evaluation')
            self.assertEqual(data_dict['year'], '2019')

    def test_parse_related_documents(self):
        """Test if given an publication listing page of the who website,
        the spider yields a request to a publication.
        """

        with open('./tests/mock_sites/nice/2.html', 'rb') as html_site:
            request = Request('http://foo.bar')
            response = HtmlResponse(
                'http://foo.bar',
                body=html_site.read(),
                request=request,
                encoding='utf-8'
            )

            res = next(self.spider.parse_article(response))

            self.assertTrue(res)
            self.assertTrue(res.meta.get('data_dict'))
            data_dict = res.meta['data_dict']
            self.assertEqual(data_dict['title'],
                             'StoneChecker for kidney stone evaluation')
            self.assertEqual(data_dict['year'], '2019')
