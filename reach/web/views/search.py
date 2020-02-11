import json
import re

from elasticsearch import ConnectionError, NotFoundError
import falcon

from reach.web.views import template


def _build_es_query(params):
    """Builds the body of the ES search query and return it as a dict.

    Args:
        params: the parameters from a web query. Should at least contain a
                terms and a fields parameter.

    Returns:
        search_body: a dict conating the body for an ES search query.
    """
    size = params.get('size', 25)
    fields = params.get('fields', '').split(',')
    terms = params.get('terms', '').split(',')

    if len(fields) > len(terms):
        # At the moment the frontend is still using "one term for all
        # fields". This will change to an exception after frontend
        # changes.
        while len(terms) < len(fields):
            terms.append(terms[0])

    body_queries = {}
    for i, fieldname in enumerate(fields):
        field = "doc.{fieldname}".format(fieldname=fieldname)
        new_terms = terms[i].lower()
        new_terms = re.sub(r'[^\w\s]', ' ', new_terms).split(' ')
        new_terms = list(filter(lambda x: len(x.strip()) > 0, new_terms))
        if field in body_queries.keys():
            body_queries[field] = body_queries[field] + new_terms
        else:
            body_queries[field] = new_terms

    terms = [
        {'terms_set': {
            key: {
                "terms": value,
                "minimum_should_match_script": {
                    "source": str(len(value))
                }
            }
        }} for key, value in body_queries.items()
    ]
    search_body = {
        'size': int(size),
        'query': {
            'bool': {
                'should': terms,
                "minimum_should_match": 1
            }
        }
    }

    if params.get('page'):
        search_body['from'] = (int(params.get('page')) - 1) * int(size)

    if params.get('sort'):
        search_body['sort'] = {
            f"doc.{params.get('sort')}": params.get('order', 'asc')
        }

    return search_body


def _search_es(es, es_index, params, explain):
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
            es.cluster.health(wait_for_status='yellow')

            search_body = _build_es_query(params)

            return True, es.search(
                index=es_index,
                body=json.dumps(search_body),
                explain=explain
            )

        except ConnectionError:
            message = 'Could not join the elasticsearch server.'
            raise falcon.HTTPServiceUnavailable(description=message)

        except NotFoundError:
            message = 'No results found.'
            return False, {'message': message}

        except Exception as e:
            raise falcon.HTTPError("400", description=str(e))


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
            if not req.params.get('terms'):
                resp.body = json.dumps({
                    'status': 'error',
                    'message': "The request doesn't contain anything to search"
                })
                resp.status = falcon.HTTP_400

            status, response = _search_es(
                self.es,
                self.es_index,
                req.params,
                self.es_explain
            )
            if status:

                if 'citation' in self.es_index:
                    # Clean dataset a bit before using in JS
                    # response = format_citation(response)
                    pass
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
        self.search_fields = ','.join([
            'title',
            'text',
            'organisation',
            'authors',
        ])

        super(FulltextPage, self).__init__(template_dir, context)

    def on_get(self, req, resp):
        if req.params:
            params = {
                "terms": req.params.get('terms', ''),
                "fields": self.search_fields,  # search_es is expects a str
                "size": int(req.params.get('size', 1)),
                "sort": "organisation",
            }

            # Still query on the backend to ensure some results are found
            status, response = _search_es(
                self.es,
                self.es_index,
                params,
                True
            )

            self.context['es_response'] = response
            self.context['es_status'] = status

            # This line will go away after frontend update
            self.context['term'] = params['terms'].split(',')[0]

            if (not status) or (response.get('message')):
                self.context.update(params)
                super(FulltextPage, self).render_template(
                    resp,
                    '/results/policy-docs',
                )
                return

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
        self.search_fields = ','.join([
            'match_title',
            'policies.title',
            'policies.organisation',
            'match_source',
            'match_publication',
            'match_authors'
        ])

        super(CitationPage, self).__init__(template_dir, context)

    def on_get(self, req, resp):
        if req.params:
            params = {
                "terms": req.params.get('terms', ''),
                "fields": self.search_fields,
                "size": int(req.params.get('size', 1)),
            }

            status, response = _search_es(
                self.es,
                self.es_index,
                params,
                False
            )

            self.context['es_response'] = response
            self.context['es_status'] = status
            self.context['term'] = params['terms'].split(',')[0]

            if (not status) or (response.get('message')):
                self.context.update(params)
                super(CitationPage, self).render_template(
                    resp,
                    '/results/citations',
                )
                return

            self.context.update(params)
            super(CitationPage, self).render_template(
                resp,
                '/results/citations',
            )
        else:
            super(CitationPage, self).on_get(req, resp)
