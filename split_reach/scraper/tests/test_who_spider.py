import os.path
import unittest

from scrapy.http import Response, Request, HtmlResponse
from scrapy.utils.project import get_project_settings
from reach.scraper.wsf_scraping.spiders.who_iris_spider import WhoIrisSpider

from .common import get_path, TEST_PDF


class Crawler:

    class Stats:
        def get_value(*args):
            return None

    stats = Stats()


class TestWhoIrisSpider(unittest.TestCase):

    def setUp(self):
        self.test_file = open(TEST_PDF, 'rb')
        self.spider = WhoIrisSpider()
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

        request = Request('http://foo.bar/documents/document.pdf', meta=meta)
        pdf_response = Response(
            'http://foo.bar/documents/document.pdf',
            body=self.test_file.read(),
            request=request,
            headers=headers
        )

        res = self.spider.save_pdf(pdf_response)
        self.assertTrue(res)
        self.assertTrue('foo' == res['title'])

    def test_parse(self):
        """Test if given an publication listing page of the who website,
        the spider yields a request to a publication, parsed by the
        parse_article function.
        """

        with open(get_path('mock_sites/who/1.html'), 'rb') as html_site:
            request = Request('http://foo.bar')
            response = HtmlResponse(
                'http://foo.bar',
                body=html_site.read(),
                request=request
            )

            res = next(self.spider.parse(response))

            # Check if something is returned
            self.assertTrue(res)

            # Check the name of the function called in callback
            self.assertEqual(res.callback.__name__, 'parse_article')

            # Check if the url is parsed and formated (site + page + param)
            self.assertEqual(
                res._url,
                'http://foo.bar/tests/mock_sites/2.html?show=full'
            )

    def test_parse_article(self):
        """Test if given an publication details page, the parse_article
        function returns details about the object and calls the
        save_pdf function.
        """

        with open(get_path('mock_sites/who/2.html'), 'rb') as html_site:
            request = Request('http://foo.bar')
            response = HtmlResponse(
                'http://foo.bar',
                body=html_site.read(),
                request=request
            )

            res = next(self.spider.parse_article(response))

            # Check if something is returned
            self.assertTrue(res)

            # Check the name of the function called in callback
            self.assertEqual(res.callback.__name__, 'save_pdf')

            # Check if the url is parsed and formated (site + page + param)
            self.assertEqual(
                res._url,
                'http://foo.bar/foo.pdf'
            )

            self.assertTrue(res.meta['data_dict'])
            data_dict = res.meta['data_dict']
            self.assertEqual(
                data_dict['title'],
                'Air pollution control: report on an inter-regional seminar '
                'convened by the World Health Organization in collaboration '
                'with the Government of the USSR'
            )

            self.assertEqual(len(data_dict), 9)
