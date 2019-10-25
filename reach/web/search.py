import json
import math

from elasticsearch import ConnectionError, NotFoundError
import falcon

from . import api
from .templates import TemplateResource


def _get_pages(current_page, last_page):
    """Return a list of pages to be used in the rendered template from the
    last page number."""
    pages = []

    if current_page > 3:
        pages.append(1)

    if current_page > 4:
        pages.append('...')
    pages.extend(
        range(
            max(current_page - 2, 1), min(current_page + 3, last_page)
        )
    )
    if current_page < last_page - 3:
        pages.append('...')

    if last_page not in pages:
        pages.append(last_page)

    return pages


def _search_es(es, params, explain=False):
        """Run a search on the elasticsearch database.

        Args:
            es: An Elasticsearch active connection.
            params: The request's parameters. Shoud include 'term' and at
                    least a field ([text|title|organisation]).
            explain: A boolean to enable|disable elasticsearch's explain.

        Returns:
            True|False: The search success status
            es.search()|str: A dict containing the result of the search if it
                             succeeded or a string explaining why it failed
        """
        try:
            fields = params.get('fields', [])
            page = params.get('page', 1)
            size = params.get('size', 50)
            es.cluster.health(wait_for_status='yellow')

            es_body = {
                'from': (page - 1) * size,
                'size': size,
                'query': {
                    'multi_match': {
                        'query': params.get('term'),
                        'type': "best_fields",
                        'fields': ['.'.join(['doc', f]) for f in fields]
                    }
                }
            }

            api.logger.info('Searching for "{query}"'.format(
                query=es_body
            ))

            return True, es.search(
                index='policy-test-docs',
                body=json.dumps(es_body),
                explain=explain
            )

        except ConnectionError:
            message = 'Could not join the elasticsearch server'
            api.logger.error(message)
            raise falcon.HTTPServiceUnavailable(description=message)

        except NotFoundError:
            message = 'No results found.'
            return False, message

        except Exception as e:
            api.logger.error(e)
            raise falcon.HTTPError(description=str(e))


class FulltextApi:
    """Let you search for terms in publications fulltexts. Returns a json.

    Args:
        es: An elasticsearch connection
        es_explain: A boolean to enable|disable elasticsearch's explain.

    """

    def __init__(self, es, es_explain):
        self.es = es
        self.es_explain = es_explain

    def on_get(self, req, resp):
        """Returns the result of a search on the elasticsearch cluster.

        Args:
            req: The request passed to this controller
            resp: The reponse object to be returned
        """
        if req.params:
            status, response = _search_es(self.es, req.params, self.es_explain)
            if status:
                response['status'] = 'success'
                resp.body = json.dumps(response)
            else:
                resp.body = json.dumps({
                    'status': 'error',
                    'message': response
                })
        else:
            resp.body = json.dumps({
                'status': 'error',
                'message': "The request doesn't contain any parameters"
            })
            resp.status = falcon.HTTP_400


class FulltextPage(TemplateResource):
    """Let you search for terms in publications fulltexts. Returns a web page.

    Args:
        es: An elasticsearch connection
        es_explain: A boolean to enable|disable elasticsearch's explain.

    """

    def __init__(self, template_dir, es, es_explain, context=None):
        self.es = es
        self.es_explain = es_explain

        super(FulltextPage, self).__init__(template_dir, context)

    def on_get(self, req, resp):
        if req.params:
            params = {
                "term": req.params['term'],
                "fields": ["text", "organisation"],
                "page": int(req.params.get('page', 1)),
                "size": int(req.params.get('size', 50)),
            }

            status, response = _search_es(self.es, params, True)

            self.context['es_response'] = response
            self.context['es_status'] = status
            self.context['pages'] = _get_pages(
                params['page'],
                math.ceil(
                    float(response['hits']['total']['value']) / params['size'])
                )

            self.context.update(params)
        super(FulltextPage, self).on_get(req, resp)
