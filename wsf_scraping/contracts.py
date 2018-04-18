# -*- coding: utf-8 -*-

from scrapy.contracts import Contract


class AjaxContract(Contract):
    """Add headers to a contract so that it becomes an ajax request."""
    name = "ajax"

    def adjust_request_args(self, kwargs):
        headers = {
            'X-Requested-With': 'XMLHttpRequest',
            'referer': 'https://www.nice.org.uk/guidance/published'
        }
        kwargs['headers'] = headers
        return kwargs
