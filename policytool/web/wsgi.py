import os
from . import api


class Configuration:
    def __init__(self):
        # Elasticsearch stuff
        assert os.environ.get('ELASTICSEARCH_HOST'), 'No elasticsearch host'
        self.es_host = os.environ['ELASTICSEARCH_HOST']
        self.es_explain = os.environ.get('ELASTICSEARCH_EXPLAIN', False)


config = Configuration()

application = api.create_api(config)
