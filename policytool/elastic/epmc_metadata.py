"""
Inserts EPMC metadata into Elasticsearch.

Sample URL for testing:

    s3://datalabs-staging/airflow/output/open-research/epmc-metadata/epmc-metadata.json.gz 
"""

import json
import logging

from . import common

ES_INDEX = 'epmc-metadata'

def to_es_action(line):
    d = json.loads(line)
    return {
        "_index": ES_INDEX,
        "doc": d,
    }


def clean_es(es):
    """ Ensure an empty index exists. """
    common.clean_es(es, ES_INDEX)


def insert_file(f, es, max_items=None):
    """
    Inserts EPMC metadata from a json.gz file into Elasticsearch.

    Args:
        f: json.gz file object
        es: a living connection to elacticsearch
        max_items: maximum number of records to insert, or None
    """

    logging.info(
        'epmc_metadata.insert_file: f=%s es=%s max_items=%s',
        f, es, max_items)
    return common.insert_actions(
        es,
        common.yield_actions(f, to_es_action, max_items),
        )


if __name__ == '__main__':
    count = common.insert_from_argv(
        __doc__.strip(), clean_es, insert_file)
    logging.info('Imported %d pubs into ES', count)
