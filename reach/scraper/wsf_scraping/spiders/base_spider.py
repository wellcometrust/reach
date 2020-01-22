import os.path
import tempfile
from urllib.parse import urlparse

from scrapy.exceptions import CloseSpider, IgnoreRequest
from scrapy.spidermiddlewares.httperror import HttpError
from scrapy.utils.project import get_project_settings
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError
import scrapy

from ..items import Article


class BaseSpider(scrapy.Spider):

    schemes = ['http', 'https', 'ftp', 'ftps']


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

    def _is_valid_pdf(self, response):
        """ Test if a response is a PDF

        We allow a pdf if it's file extension is not .pdf but
        its content-type is explicitly `application/pdf`

        Args:
            response: The request response
            extension: The type of extension to limit to
            mimetype: Either a **list|tuple** of or single mimetype
                      to limit the URL to
        """

        # Check the headers of the response
        is_pdf_type, is_octet_type = self._get_response_typing(response)

        if is_pdf_type:
            return True

        if is_octet_type:
            # If the response is an octet, make sure its a pdf
            # as this could result in trying to download images,
            # word docs, powerpoints, etc...
            url = response.urljoin(response.request.url)
            return self._is_valid_pdf_url(url)
        else:
            return False

    def _get_response_typing(self, response):
        """ Test if a response has valid content-type headers

        Args:
            response: HTTP request response
        """
        response_headers = response.headers
        content_type = response_headers.get('content-type', '').split(b';')[0]

        is_pdf_type = b'application/pdf' == content_type
        is_octet_type = b'application/octet-stream' == content_type

        return (is_pdf_type, is_octet_type)


    def _is_valid_pdf_url(self, url):
        """ Check if a URL represents a valid URL path

        Args:
            url: The URL to test
        """
        if url in ('', None,):
            return False

        try:
            scheme, netloc, path, params, query, fragment = urlparse(url)
        except ValueError: # For example invalid IPV6 URL or something
            return False

        if scheme != '' and scheme not in self.schemes:
            return False

        if not path.lower().endswith(".pdf"):
            return False

        return True

    def save_pdf(self, response, allow_octet=False):
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

        # Handle application/octet-stream in case some servers
        # don't provide a specific content-type in the response
        # as well as verify that path belongs to a PDF file.
        is_pdf = self._is_valid_pdf(response)

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

        # Try and get filename from Content-Disposition
        disposition_name = None
        cd_header = response.headers.get("Content-Disposition", None)
        if cd_header:
            cd_items = [x.split(b"=") for x in cd_header.split(b';')[1:] if b"=" in x]
            cd_items = dict((item[0].lower(), item[1] or None) for item in cd_items if item[0] is not None)
            disposition_name = cd_items.get(b"name", None)
            if disposition_name is None:
                disposition_name = cd_items.get(b"filename", None)
            if disposition_name is None:
                disposition_name = cd_items.get(b'filename*', None)

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

        # TODO: Get the filename from Content-Disposition header if available
        article = Article({
            'title': data_dict.get('title', None),
            'url': response.request.url,
            'url_filename': response.request.url.split("/")[-1],
            'year': data_dict.get('year', None),
            'authors': data_dict.get('authors', None),
            'types': data_dict.get('types', None),
            'subjects': data_dict.get('subjects', None),
            'pdf': filename,
            'page_title': data_dict.get('page_title', None),
            'source_page': data_dict.get('source_page', None),
            'link_title': data_dict.get('link_text', None),
            'page_headings': data_dict.get('page_headings', None),
            'disposition_title': disposition_name
        })

        return article
