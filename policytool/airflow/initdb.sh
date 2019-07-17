#!/bin/sh -e

if echo $AIRFLOW__CORE__SQL_ALCHEMY_CONN | grep -q postgres
then
    if ! /src/policytool/scraper/pg_exists.py dag; then
        # airflow upgradedb gets us a working DB from empty, but without all
        # the extra connections.
        # cf. https://medium.com/datareply/airflow-lesser-known-tips-tricks-and-best-practises-cf4d4a90f8f
        airflow upgradedb
    fi
else
    echo $AIRFLOW__CORE__SQL_ALCHEMY_CONN
    echo "initdb.sh: Unsupported DSN!" >&2
    exit 1
fi
