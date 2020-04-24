import os
from . import api


class Configuration:
    def __init__(self):
        """
        Parses webapp configuration from the environment. Key variables:

        - ELASTICSEARCH_HOST
        - ELASTICSEARCH_EXPLAIN
        - ELASTICSEARCH_POLICYDOCS_INDEX
        - ELASTICSEARCH_CITATIONS_INDEX
        - STATIC_ROOT
        """

        self.database_url = os.environ['DATABASE_URL']
        if not self.database_url or not os.path.isdir(self.database_url):
            raise Exception(
                "Database URL not found. DATABASE_URL=%r" %
                self.database_url
            )

        self.static_root = os.environ.get('STATIC_ROOT')
        if not self.static_root or not os.path.isdir(self.static_root):
            raise Exception(
                "No static directory found. STATIC_ROOT=%r" %
                self.static_root
            )

        self.docs_static_root = os.environ.get('DOCS_STATIC_ROOT')
        if not self.docs_static_root or not os.path.isdir(
            self.docs_static_root
        ):
            raise Exception(
                "No docs static directory found. DOCS_STATIC_ROOT=%r" %
                self.docs_static_root
            )


config = Configuration()
application = api.create_api(config)
