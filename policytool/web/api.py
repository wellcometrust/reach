"""
Entrypoint for web UI & API. Run with:

    gunicorn --reload web.api:api

"""

import logging
import os
import os.path
from urllib.parse import urlparse

import falcon
from elasticsearch import Elasticsearch

from .templates import TemplateResource
from . import search

TEMPLATE_ROOT = os.path.join(os.path.dirname(__file__), 'templates')


def configure_logger(logger):
    """ Configures our logger w/same settings & handler as our webserver
    (always gunicorn).
    """
    gunicorn_logger = logging.getLogger('gunicorn.error')
    logger.handlers = gunicorn_logger.handlers
    logger.setLevel(gunicorn_logger.level)


# Logging
logger = logging.getLogger()
configure_logger(logger)


def get_context(os_environ):
    return {
        'POLICYTOOL_VERSION': os_environ.get(
            'POLICYTOOL_VERSION', 'development'
        )
    }


def create_api(conf):
    """
    Args:
        Configuration object, as defined in policytool.web.wsgi

    Returns:
        WSGI application
    """
    parsed_url = urlparse(conf.es_host)

    logger.info('Connecting to {elastic_host}'.format(
        elastic_host=conf.es_host
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
        '/search/citations',
        TemplateResource(TEMPLATE_ROOT, get_context(os.environ))
    )
    api.add_route(
        '/search/content',
        TemplateResource(TEMPLATE_ROOT, get_context(os.environ))
    )
    api.add_route(
        '/results/content',
        search.FulltextPage(TEMPLATE_ROOT, es, conf.es_explain,
                            get_context(os.environ))
    )
    api.add_route(
        '/api/search',
        search.FulltextApi(es, conf.es_explain)
    )
    api.add_static_route('/static', conf.static_root)
    return api
