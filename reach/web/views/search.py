import json
import math

from elasticsearch import ConnectionError, NotFoundError
import falcon

from reach.web.views import template
from reach.web import api


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


def _search_es(es, es_index, params, explain=False):
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
            fields = params.get('fields', '').split(',')
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

            return True, es.search(
                index=es_index,
                body=json.dumps(es_body),
                explain=explain
            )

        except ConnectionError:
            message = 'Could not join the elasticsearch server.'
            raise falcon.HTTPServiceUnavailable(description=message)

        except NotFoundError:
            message = 'No results found.'
            return False, {'message': message}

        except Exception as e:
            raise falcon.HTTPError(description=str(e))


class SearchApi:
    """Let you search for terms in publications fulltexts. Returns a json.

    Args:
        es: An elasticsearch connection
        es_index: The index to search on
        es_explain: A boolean to enable|disable elasticsearch's explain.

    """

    def __init__(self, es, es_index, es_explain):
        self.es = es
        self.es_index = es_index
        self.es_explain = es_explain

    def on_get(self, req, resp):
        """Returns the result of a search on the elasticsearch cluster.

        Args:
            req: The request passed to this controller
            resp: The reponse object to be returned
        """
        if req.params:
            status, response = _search_es(
                self.es,
                self.es_index,
                req.params,
                self.es_explain
            )
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


class FulltextPage(template.TemplateResource):
    """Let you search for terms in publications fulltexts. Returns a web page.

    Args:
        es: An elasticsearch connection
        es_explain: A boolean to enable|disable elasticsearch's explain.

    """

    def __init__(self, template_dir, es, es_index, es_explain, context=None):
        self.es = es
        self.es_index = es_index
        self.es_explain = es_explain

        super(FulltextPage, self).__init__(template_dir, context)

    def on_get(self, req, resp):
        if req.params:
            params = {
                "term": req.params.get('term', ''),  # es returns none on empty
                "fields": "text,organisation",  # search_es is expects a str
                "page": int(req.params.get('page', 1)),
                "size": int(req.params.get('size', 20)),
            }

            status, response = _search_es(self.es, self.es_index, params, True)

            self.context['es_response'] = response
            self.context['es_status'] = status

            if (not status) or (response.get('message')):
                self.context.update(params)
                super(FulltextPage, self).render_template(
                    resp,
                    '/results/policy-docs',
                )
                return

            self.context['pages'] = _get_pages(
                params['page'],
                math.ceil(
                    float(response['hits']['total']['value']) / params['size'])
                )

            self.context.update(params)
            super(FulltextPage, self).render_template(
                resp,
                '/results/policy-docs',
            )
        else:
            super(FulltextPage, self).on_get(req, resp)


class CitationPage(template.TemplateResource):
    """Let you search for terms in publications citations. Returns a web page.

    Args:
        es: An elasticsearch connection
        es_explain: A boolean to enable|disable elasticsearch's explain.

    """

    def __init__(self, template_dir, es, es_index, es_explain, context=None):
        self.es = es
        self.es_index = es_index
        self.es_explain = es_explain

        super(CitationPage, self).__init__(template_dir, context)

    def on_get(self, req, resp):
        if req.params:
            params = {
                "term": req.params.get('term', ''),  # es returns none on empty
                "fields": "Extracted title,Matched title,Document id",
                "page": int(req.params.get('page', 1)),
                "size": int(req.params.get('size', 20)),
            }

            status, response = _search_es(self.es, self.es_index, params, True)

            self.context['es_response'] = response
            self.context['es_status'] = status

            if (not status) or (response.get('message')):
                self.context.update(params)
                super(CitationPage, self).render_template(
                    resp,
                    '/results/citations',
                )
                return

            self.context['pages'] = _get_pages(
                params['page'],
                math.ceil(
                    float(response['hits']['total']['value']) / params['size'])
                )

            self.context.update(params)
            super(CitationPage, self).render_template(
                resp,
                '/results/citations',
            )
        else:
            super(CitationPage, self).on_get(req, resp)
