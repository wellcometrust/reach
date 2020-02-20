#!/usr/bin/env python3

"""
Tests for whether something exists in postgres or not.
"""

import argparse
import logging
import os
import sys

import psycopg2

CONNECT_TIMEOUT = 1

parser = argparse.ArgumentParser(description=__doc__.strip())
parser.add_argument('tablename')
parser.add_argument('-v', dest='verbose', action='store_true')


def check_table(dsn, tablename):
    with psycopg2.connect(dsn, connect_timeout=CONNECT_TIMEOUT) as con:
        with con.cursor() as c:
            c.execute(
                'SELECT 1 FROM pg_tables '
                'WHERE schemaname = %s AND tablename = %s',
                ('public', tablename)
            )
            if c.fetchone() == (1,):
                return 0
    return 1


if __name__ == '__main__':
    args = parser.parse_args()
    logging.basicConfig()
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)

    if 'POSTGRES_DSN' not in os.environ:
        logging.error('Error: POSTGRES_DSN not set')
        sys.exit(2)

    result = check_table(os.environ['POSTGRES_DSN'], args.tablename)
    sys.exit(result)
