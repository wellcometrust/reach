#!/usr/bin/env python3

"""
Executes a command when postgres is ready, or exits 1 if it's not ready
after the timeout.

Here, "ready" means:

1. We can connect to postgres on $POSTGRES_DSN, and
1. We can run a query (SELECT 1;) for > (success-secs), to accomodate
   postgres initialization scripts that restart the DB.
"""

import argparse
import logging
import os
import sys
import time

import psycopg2

CONNECT_TIMEOUT = 1
POLL_WAIT = 0.5

parser = argparse.ArgumentParser(description=__doc__.strip())
parser.add_argument('--timeout', type=int, default=15)
parser.add_argument('--success-secs', type=float, default=5)
parser.add_argument('-v', dest='verbose', action='store_true')
parser.add_argument('args', nargs=argparse.REMAINDER)


def test_connection(dsn):
    with psycopg2.connect(dsn, connect_timeout=CONNECT_TIMEOUT) as con:
        with con.cursor() as c:
            c.execute('SELECT 1')


def pg_isready(dsn, timeout, success_secs):
    start = time.time()
    while time.time() - start < timeout:
        try:
            success_start = time.time()
            while time.time() - success_start < success_secs:
                if time.time() - start > timeout:
                    return 1
                test_connection(dsn)
                logging.debug('pg_isready: successful connect')
                time.sleep(POLL_WAIT)
            return 0
        except psycopg2.OperationalError as e:
            logging.debug('pg_isready: %s', e)
            time.sleep(POLL_WAIT)
    return 1


if __name__ == '__main__':
    args = parser.parse_args()
    logging.basicConfig()
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)

    if args.success_secs > args.timeout:
        logging.error(
            'pg_isready: timeout time is lower than success secs. Failing'
        )
        sys.exit(2)

    if 'POSTGRES_DSN' not in os.environ:
        logging.error('Error: POSTGRES_DSN not set')
        sys.exit(2)

    result = pg_isready(
        os.environ['POSTGRES_DSN'], args.timeout, args.success_secs)
    if result != 0:
        logging.error(
            'pg_isready: queries did not succeeed after %ss. Failing',
            args.timeout
        )
        sys.exit(result)
    os.execvp(args.args[0], args.args)
