"""
Entrypoint for web UI & API. Run with:

    gunicorn --reload web.api:api

"""

import logging
import os
import os.path
from urllib.parse import urlparse

import falcon
import jinja2
from elasticsearch import Elasticsearch

from . import search

TEMPLATE_ROOT = os.path.join(os.path.dirname(__file__), 'templates')
STATIC_ROOT = os.environ.get('STATIC_ROOT')
if not STATIC_ROOT or not os.path.isdir(STATIC_ROOT):
    raise Exception("No static directory found. STATIC_ROOT=%r" % STATIC_ROOT)


def configure_logger(logger):
    """ Configures our logger w/same settings & handler as our webserver
    (always gunicorn).
    """
    gunicorn_logger = logging.getLogger('gunicorn.error')
    logger.handlers = gunicorn_logger.handlers
    logger.setLevel(gunicorn_logger.level)


def to_template_names(path):
    """
    Maps HTTP request paths to Jinja template paths.

    Args:
        path: path portion of HTTP GET request

    Returns:
        Tuple of file paths that Jinja should search for.
    """

    if not path.startswith('/'):
        raise ValueError
    path = path[1:]  # remove leading /, jinja won't want it

    if os.path.basename(path).startswith('_'):
        # Macros are kept in templates starting with _; don't allow
        # access to them.
        return tuple()

    if path == '':
        return ('index.html',)

    if path.endswith('/'):
        return (
            path[:-1] + '.html',
            os.path.join(path, 'index.html'),
        )

    if path.endswith('.html'):
        return (
            path,
            os.path.join(path[:-5], 'index.html'),
        )

    return (
        path + '.html',
        os.path.join(path, 'index.html'),
    )


def get_context(os_environ):
    return {
        'POLICYTOOL_VERSION': os_environ.get(
            'POLICYTOOL_VERSION', 'development'
        )
    }


class TemplateResource:
    """
    Serves HTML templates. Note that templates are read from the FS for
    every request.
    """

    def __init__(self, template_dir, context=None):
        logger.info('TemplateResource: template_dir=%s', template_dir)
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir),
            autoescape=jinja2.select_autoescape(['html']),
        )
        if context is not None:
            self.context = context
        else:
            self.context = {}

    def on_get(self, req, resp):
        tnames = to_template_names(req.path)
        try:
            template = self.env.select_template(tnames)
            resp.body = template.render(**self.context)
            resp.content_type = 'text/html'
        except jinja2.TemplateNotFound:
            resp.status = falcon.HTTP_404
            return


# Logging
logger = logging.getLogger()
configure_logger(logger)

# Elasticsearch stuff
assert os.environ.get('ELASTICSEARCH_HOST'), 'No elasticsearch host'
parsed_url = urlparse(os.environ['ELASTICSEARCH_HOST'])

logger.info('Connecting to {elastic_host}'.format(
    elastic_host=os.environ['ELASTICSEARCH_HOST']
))
es = Elasticsearch([{
        'host': parsed_url.hostname,
        'port': parsed_url.port
    }],
)

# Routes (are LIFO)
api = falcon.API()
api.add_route(
    '/',
    TemplateResource(TEMPLATE_ROOT, get_context(os.environ))
)
api.add_route(
    '/search',
    search.Fulltext(es)
)
api.add_static_route('/static', STATIC_ROOT)
