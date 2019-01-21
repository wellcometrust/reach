import scrapy
import os
import tempfile
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError
from urllib.parse import urlparse


class BaseSpider(scrapy.Spider):

    def __init__(self, *args, **kwargs):
        id = kwargs.get('uuid', '')
        self.uuid = id

    def on_error(self, failure):

        if failure.check(HttpError):
            response = failure.value.response
            self.logger.error('HttpError on %s', response.url)

        elif failure.check(DNSLookupError):
            request = failure.request
            self.logger.error('DNSLookupError on %s', request.url)

        elif failure.check(TimeoutError):
            request = failure.request
            self.logger.error('TimeoutError on %s', request.url)

        else:
            self.logger.error(repr(failure))

    def _check_headers(self, response_headers,
                       desired_extension=b'application/pdf'):
        content_type = response_headers.get('content-type', '').split(b';')[0]
        return desired_extension == content_type

    def _save_file(self, url, response_body):
        filename = os.path.basename(urlparse(url).path)
        tempdir = tempfile.mkdtemp()
        if filename:
            if not filename.lower().endswith('.pdf'):
                filename = filename + '.pdf'
            filepath = os.path.join(tempdir, filename)
            with open(filepath, 'wb') as f:
                f.write(response_body)
            return filepath
        else:
            self.logger.warning(
                 'Empty filename, could not save the file. [Url: %s]',
                 url
            )
            return ''
