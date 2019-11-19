# -*- coding: utf-8 -*-
import os
import logging
import sentry_sdk
from twisted.python import log
from scrapy import signals
from scrapy import logformatter
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



class ReachOffsiteMiddleware(OffsiteMiddleware):
    """ Overridden scrapy.middlewares.offsite.OffsiteMiddleware
    to provide some custom functionality
    """

    def should_follow(self, request, spider):
        """ Overridden to alow support for a custom `disallowed_domains`
        class property in the sub-classed reach spiders to stop the crawler
        from hitting known problematic offsite routes
        """

        regex = self.host_regex
        disallowed_hosts = getattr(spider, 'disallowed_hosts', None)
        # hostname can be None for wrong URLs (like javascript links)
        host = urlparse_cached(request).hostname or ''

        if disallowed_hosts and host in disallowed_hosts:
            logger.warn(
                "Filtered offsite request to %(domain)r: %(request)s",
                {'domain': host, 'request': x}, extra={'spider': spider})
            return False

        return bool(regex.search(host))



