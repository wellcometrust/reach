# -*- coding: utf-8 -*-
import os
import logging
import sentry_sdk
from twisted.python import log
from scrapy import signals
from scrapy import logformatter
from scrapy.http import Request
from scrapy.spidermiddlewares.offsite import OffsiteMiddleware
from scrapy.utils.httpobj import urlparse_cached


sentry_sdk.init(os.getenv('SENTRY_DSN'))


def log_to_sentry(event):
    if not event.get('isError') or 'failure' not in event:
        return

    f = event['failure']
    sentry_sdk.capture_exception((f.type, f.value, f.getTracebackObject()))


log.addObserver(log_to_sentry)
logger = logging.getLogger(__name__)


class PoliteLogFormatter(logformatter.LogFormatter):
    def dropped(self, item, exception, response, spider):
        return {
            'level': logging.DEBUG,
            'msg': logformatter.DROPPEDMSG,
            'args': {
                'exception': exception,
                'item': item,
            }
        }


class WsfScrapingSpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        # spider.logger.info('Spider opened: %s' % spider.name)
        pass


class ReachDisallowedHostMiddleware(object):
    """ Provides additional functionality to sub-classes spiders
    to explicity block crawling hosts which are known to be problematic
    through the `disallowed_hosts` class property.

    `disallowed_hosts` must be explicit about the domain being blocked,
    for instance for the domain gov.uk, you should include both
    www.gov.uk and gov.uk in the disallowed_hosts property.
    """

    def __init__(self, stats):
        self.stats = stats

    @classmethod
    def from_crawler(cls, crawler):
        o = cls(crawler.stats)
        crawler.signals.connect(o.spider_opened, signal=signals.spider_opened)
        return o

    def spider_opened(self, spider):
        self.domains_seen = set()

    def process_spider_output(self, response, result, spider):
        """ Process the output from a spider and filter out any requests which
        may lead to hosts we have explicitly disallowed in the
        `disallowed_hosts` property of the spider

        Args:
            response: The response from the crawl
            result: A list of requests that are prepped from the response
            spider: The spider instance doing the crawl
        """
        disallowed_hosts = getattr(spider, 'disallowed_hosts', [])

        for x in result:
            if isinstance(x, Request):
                domain = urlparse_cached(x).hostname
                if domain and domain in disallowed_hosts:
                    # The domain is a disallowed one
                    if domain not in self.domains_seen:
                        # We only fire this once for every time we come
                        # across a domain that we're filtering
                        self.domains_seen.add(domain)
                        logger.debug(
                            " Filtered request to %(domain)s: %(request)s",
                            {'domain': domain, 'request': x}, extra={'spider': spider})
                        self.stats.inc_value('disallowed/domains', spider=spider)

                    self.stats.inc_value('disallowed/filtered', spider=spider)
                else:
                    # We're not filtering this domain
                    yield x
            else:
                # Not a request, yield it
                yield x
