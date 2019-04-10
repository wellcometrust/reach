#!/bin/sh -e

initdb() {
    airflow initdb
    # delete default connections created by initdb; we don't use them
    CONNECTIONS=$(airflow connections  -l | grep -vE '^\[' | grep -v 'Conn Id' | \
      awk '{print $2}' | tr -d "'" )
    if [ -n "$CONNECTIONS" ]; then
      echo $CONNECTIONS | xargs -n1 airflow connections -d --conn_id
    fi
}

if echo $AIRFLOW__CORE__SQL_ALCHEMY_CONN | grep -q postgres
then
    if ! /src/datalabs/pg_exists.py dag; then
        initdb
    fi
else
    echo $AIRFLOW__CORE__SQL_ALCHEMY_CONN
    echo "initdb.sh: Unsupported DSN!" >&2
    exit 1
fi
