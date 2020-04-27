import json

import falcon

from web.views import template


DEFAULT_SORTING = {
    "citation": "match_title",
    "policy_doc": "title",
}


def _build_psql_query(params, source):
    """Prepare the query and arguments to be sent to PostgreSQL.

    Args:
        params: the parameters from a web query. Should at least contain a
                terms and a fields parameter.

        source: the table to query.

    Returns:
        query: a dict containing the results for a PSQL search query.
        terms: the args to send to postgres
    """
    size = params.get('size', 25)
    fields = params.get('fields', '').split(',')
    terms = params.get('terms', '').split(',')

    query = """
        SELECT {fields}
        FROM {source}
        WHERE {where_query}
        ORDER BY {order}
        {is_asc}
        LIMIT {size}
        OFFSET {offset};
    """

    query.format(
        fields=', '.join(fields),
        source=source,
        where_query='=%d OR '.join(fields),
        order=params.get('sort', DEFAULT_SORTING[source]),
        is_asc=params.get('order', 'ASC'),
        size=size,
        offset=(int(params.get('page')) - 1) * int(size)
    )

    return query, terms


def _search_db(db, params, source):
        """Run a search on the postgresql database.

        Args:
            db: A PostgreSQL active connection.
            params: The request's parameters. Shoud include 'term' and at
                    least a field ([text|title|organisation]).
            source: the table to query.

        Returns:
            True|False: The search success status
            es.search()|str: A dict containing the result of the search if it
                             succeeded or a string explaining why it failed
        """
        try:

            search_query, args = _build_psql_query(params, source)

            return True, db.get(search_query, args)

        except Exception as e:
            raise falcon.HTTPError("400", description=str(e))


class SearchApi:
    """Let you search for terms in publications fulltexts. Returns a json.

    Args:
        es: An elasticsearch connection
        es_index: The index to search on
        es_explain: A boolean to enable|disable elasticsearch's explain.

    """

    def __init__(self, db, source):
        self.db = db
        self.source = source

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

            status, response = _search_db(self.db, req.params, self.source)
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

    def __init__(self, template_dir, db, source, context=None):
        self.db = db
        self.source = source
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
                "fields": self.search_fields,  # search_db is expects a str
                "size": int(req.params.get('size', 1)),
                "sort": "organisation",
            }

            # Still query on the backend to ensure some results are found
            status, response = _search_db(self.db, params, self.source)

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

    def __init__(self, template_dir, db, source, context=None):
        self.db = db
        self.source = source
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

            status, response = _search_db(self.db, params, self.source)

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
