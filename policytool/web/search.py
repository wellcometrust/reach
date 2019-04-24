import json

import falcon

from elasticsearch import ConnectionError, NotFoundError
from web import api


class Fulltext(object):
    """Let you search for terms in publications fulltexts.

    Args:
        es: An elasticsearch connection
    """

    def __init__(self, es):
        self.es = es

    def search_es(self, req_params):
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
                explain=True
            )

        except ConnectionError:
            message = 'Could not join the elasticsearch server'
            api.logger.error(message)
            return False, message

        except NotFoundError:
            message = 'No results found.'
            return False, message

        except Exception as e:
            return False, str(e)

    def on_get(self, req, resp):
        """Returns the result of a search on the elasticsearch cluster.

        Args:
            req: The request passed to this controller
            resp: The reponse object to be returned
        """
        if req.params:
            status, response = self.search_es(req.params)
            if status:
                resp.body = json.dumps(response)
            else:
                resp.body = json.dumps({
                    'status': 'error',
                    'message': response
                })
        else:
            resp.body = json.dumps({
                'status': 'error'
            })
            resp.status = falcon.HTTP_200
