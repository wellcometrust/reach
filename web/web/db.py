import psycopg2
from contextlib import contextmanager

from psycopg2.extras import RealDictCursor
from psycopg2.pool import ThreadedConnectionPool

from web import config as conf

pool = None
MIN_CONNS = 1
MAX_CONNS = 30

def create_pool():
    global pool

    if pool is None:
        pool = ThreadedConnectionPool(
                conf.CONFIG.min_conns,
                conf.CONFIG.max_conns,
                database=conf.CONFIG.db_name,
                user=conf.CONFIG.db_user,
                password=conf.CONFIG.db_password,
                host=conf.CONFIG.db_host,
                port=conf.CONFIG.db_port,
            )
    return pool

@contextmanager
def get_db_connection():
    """ Yields a database connection from the pool
    """
    connection = None
    try:
        if pool is None:
            create_pool()
        connection = pool.getconn()
        yield connection
    finally:
        pool.putconn(connection)

@contextmanager
def get_db_cur(commit=False, name=None):
    """ Yields a cursor against the database

    Args:
        commit: Whether to commit at the end of a transaction
    """
    with get_db_connection() as connection:
        cursor = connection.cursor(cursor_factory=RealDictCursor, name=name)
        try:
            yield cursor
            if commit:
                connection.commit()
        finally:
            cursor.close()

