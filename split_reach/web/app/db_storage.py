import psycopg2

from psycopg2.extras import RealDictCursor


class StorageEngine():

    def __init__(self, database_url):
        """Builds a connection object to the given PSQL database."""
        self.conn = psycopg2.connect(
            database_url,
            cursor_factory=RealDictCursor
        )

    def get(self, query, params):
        """Returns all PSQL rows from a given query and its arguments."""
        with self.conn.cursor() as cursor:
            cursor.execute(query, tuple(params))
            results = cursor.fetchall()

        return results

    def _get_cur(self):
        return self.conn.cursor()
