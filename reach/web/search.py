import json

from elasticsearch import ConnectionError, NotFoundError
import falcon

from . import api


class Fulltext:
    """Let you search for terms in publications fulltexts.

    Args:
        es: An elasticsearch connection
    """

    def __init__(self, es, es_explain):
        self.es = es
        self.es_explain = es_explain

    def _search_es(self, req_params):
        """Run a search on the elasticsearch database.

        Args:
            req_params: The request's parameters. Shoud include 'term' and at
                        least a field (on of [text|title|organisation])

        Returns:
            True|False: The search success status
            es.search()|str: A dict containing the result of the search if it
                             succeeded or a string explaining why it failed
        """
        try:
            fields = req_params.get('fields', [])
            self.es.cluster.health(wait_for_status='yellow')

            es_body = {
                'query': {
                    'multi_match': {
                        'query': req_params.get('term'),
                        'fields': fields
                    }
                }
            }

            api.logger.info('Searching for "{query}"'.format(
                query=es_body
            ))

            return True, self.es.search(
                index='datalabs-fulltexts',
                body=json.dumps(es_body),
                explain=self.es_explain
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

    def on_get(self, req, resp):
        """Returns the result of a search on the elasticsearch cluster.

        Args:
            req: The request passed to this controller
            resp: The reponse object to be returned
        """
        if req.params:
            status, response = self._search_es(req.params)
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
