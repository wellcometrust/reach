from functools import wraps
import os

import sentry_sdk


def init_sentry_sdk(sentry_dsn):
    kwargs = {
        'integrations': [],  # we'll add celery & flask eventually here
        'default_integrations': True,
    }
    sentry_sdk.init(sentry_dsn)


def report_exception(f):
    """ Minimal decorator for reporting exceptions that occur within a
    function. Does not support generators."""
    @wraps(f)
    def wrapped_f(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except:
            sentry_sdk.capture_exception()
            raise

    return wrapped_f


# SENTRY_DSN must be present at import time. If we don't have it then,
# we won't have it later either.
init_sentry_sdk(os.environ['SENTRY_DSN'])
