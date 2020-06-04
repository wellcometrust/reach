import collections
import time

import falcon

Argument = collections.namedtuple("Argument", ('resource', 'window_size',
    'per_second', 'error_message'))

class _RateLimitDB(object):
    _RATE_LIMIT_DB = collections.defaultdict(
        lambda: collections.defaultdict(list)
    )

    @staticmethod
    def filter(user, resource_name, window_size):
        p = _RateLimitDB._RATE_LIMIT_DB[user][resource_name]
        t = time.time()
        exp_int = t - window_size
        p = [s for s in p if s >= exp_int]
        _RateLimitDB._RATE_LIMIT_DB[user][resource_name] = p

    @staticmethod
    def add_call(user, resource_name):
        _RateLimitDB._RATE_LIMIT_DB[user][resource_name].append(
            time.time()
        )

    @staticmethod
    def check_for(user, argument):
        _RateLimitDB.filter(user, argument.resource, argument.window_size)
        _RateLimitDB.add_call(user, argument.resource)
        p = len(_RateLimitDB._RATE_LIMIT_DB[user][argument.resource])
        return (p / argument.window_size) > argument.per_second

def _rate_db(req, resp, argument):
    if _RateLimitDB.check_for(req.forwarded_host, argument):
        print("RATE_LIMITED")
        resp.status = falcon.HTTP_429
        raise falcon.HTTPTooManyRequests(argument.error_message)

def rate_limit(per_second=30, resource=u'default', window_size=10,
        error_message="429 Too Many Requests"):
    arg = Argument(resource, window_size, per_second, error_message)

    def hook(req, resp, resource, params):
        _rate_db(req, resp, arg)

    return hook
