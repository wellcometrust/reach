import os.path
import tempfile

from scrapy.exceptions import CloseSpider, IgnoreRequest
from scrapy.spidermiddlewares.httperror import HttpError
from scrapy.utils.project import get_project_settings
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError
import scrapy

from ..items import Article


class BaseSpider(scrapy.Spider):

    @staticmethod
    def jobdir(scraper_name):
        return os.path.join(
            # NB: tried to use get_project_settings()['FEED_TEMPDIR']
            # here, but it was inexplicably None. Anywhere in /tmp is
            # fine though.
            '/tmp',
            'crawls',
            scraper_name
        )

    def __init__(self, *args, **kwargs):
        id = kwargs.get('uuid', '')
        self.uuid = id

    def on_error(self, failure):

        if failure.check(HttpError):
            response = failure.value.response
            self.logger.warning('HttpError (%s) on %s',
                                response.url, response.status)

        elif failure.check(DNSLookupError):
            request = failure.request
            self.logger.warning('DNSLookupError on %s', request.url)

        elif failure.check(TimeoutError):
            request = failure.request
            self.logger.warning('TimeoutError on %s', request.url)

        # Catch the case where robots.txt files forbid a page
        elif failure.check(IgnoreRequest):
            request = failure.request
            self.logger.warning('Robots.txt forbidden on %s', request.url)

        else:
            self.logger.error(repr(failure))

    def _check_headers(self, response_headers,
                       desired_extension=b'application/pdf'):
        content_type = response_headers.get('content-type', '').split(b';')[0]
        return desired_extension == content_type

    def save_pdf(self, response):
        """ Save the response body to a temporary PDF file.

        If the response body is PDF-typed, save the PDF to a tempfile to parse
        it later. Else, just drop te item.

        The item will be later deleted in the pipeline.py file.

        Args:
            - response: The reponse object passed by scrapy

        Returns:
            - A scrapy Article item.
        """

        data_dict = response.meta.get('data_dict', {})

        is_pdf = self._check_headers(response.headers)

        if not is_pdf:
            self.logger.info('Not a PDF, aborting (%s)', response.url)
            return

        if not response.body:
            self.logger.warning(
                'Empty filename or content, could not save the file.'
                ' [Url: %s]',
                response.request.url
            )
            return

        max_article = self.settings.getint('MAX_ARTICLE')
        current_item_count = self.crawler.stats.get_value('item_scraped_count')
        if max_article > 0 and current_item_count:
            if current_item_count >= max_article:
                raise CloseSpider(
                    'Specified article count ({max_article}) raised'.format(
                        max_article=max_article,
                    )
                )

        # Download PDF file to /tmp
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            tf.write(response.body)
            filename = tf.name

        article = Article({
            'title': data_dict.get('title'),
            'uri': response.request.url,
            'year': data_dict.get('year'),
            'authors': data_dict.get('authors'),
            'types': data_dict.get('types'),
            'subjects': data_dict.get('subjects'),
            'pdf': filename,
        })

        return article
