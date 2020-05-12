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

from hooks.sentry import report_exception
from web.views import template
from web.views import apidocs
from web.views import search
from web.views import search_exports
from web.views import robotstxt

TEMPLATE_ROOT = os.path.join(os.path.dirname(__file__), 'templates')
API_DOCS_ROOT = os.path.join(os.path.dirname(__file__), 'docs/build/html')


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
        'REACH_VERSION': os_environ.get(
            'REACH_VERSION', 'development'
        )
    }


@report_exception
def create_api(conf):
    """
    Args:
        Configuration object, as defined in web.wsgi

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
        template.TemplateResource(TEMPLATE_ROOT, get_context(os.environ))
    )
    api.add_route('/robots.txt', robotstxt.RobotsTxtResource())

    api.add_route(
        '/about',
        template.TemplateResource(TEMPLATE_ROOT, get_context(os.environ))
    )
    api.add_route(
        '/how-it-works',
        template.TemplateResource(TEMPLATE_ROOT, get_context(os.environ))
    )
    api.add_route(
        '/search/citations',
        search.CitationPage(
            TEMPLATE_ROOT,
            es,
            conf.es_citations_index,
            conf.es_explain,
            get_context(os.environ)
        )
    )
    api.add_route(
        '/search/policy-docs',
        search.FulltextPage(
            TEMPLATE_ROOT,
            es,
            conf.es_policy_docs_index,
            conf.es_explain,
            get_context(os.environ))
    )
    api.add_route(
        '/api/search/policy-docs',
        search.SearchApi(es, conf.es_policy_docs_index, conf.es_explain)
    )
    api.add_route(
        '/api/search/citations',
        search.SearchApi(es, conf.es_citations_index, conf.es_explain)
    )
    api.add_route(
        '/api/docs/{name}',
        apidocs.APIDocRessource(API_DOCS_ROOT, get_context(os.environ))
    )
    api.add_static_route('/api/docs/_static', conf.docs_static_root)
    api.add_route(
        '/search/citations/{ftype}',
        search_exports.CitationsExport(
            es,
            conf.es_citations_index,
            conf.es_explain
        )
    )
    api.add_route(
        '/search/policy-docs/{ftype}',
        search_exports.PolicyDocsExport(
            es,
            conf.es_policy_docs_index,
            conf.es_explain
        )
    )
    api.add_static_route('/static', conf.static_root)
    return api
