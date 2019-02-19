#!/bin/sh -e
# NB: this file is not volume'd in, so you must build the image
# after editing it.

if echo $AIRFLOW__CORE__SQLALCHEMY_CONN | grep -q sqlite
then
    sqlite_path=$(
        echo $AIRFLOW__CORE__SQLALCHEMY_CONN | sed -e 's+^sqlite://++'
    )
    echo $sqlite_path
    if ! [ -f $sqlite_path ]
    then
        airflow initdb
        # delete default connections not for AWS
        airflow connections  -l | \
          awk '{print $2}' | tr -d "'" | \
          xargs -n1 airflow connections -d --conn_id
    fi
else
    echo "Unsupported DSN!" >&2
    exit 1
fi


