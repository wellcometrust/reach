"""
Inserts EPMC metadata into Elasticsearch.

Sample URL for testing:

    s3://datalabs-staging/airflow/output/open-research/epmc-metadata/epmc-metadata.json.gz
"""

import json
import logging
import functools

from . import common

ES_INDEX = 'epmc-metadata'
CHUNK_SIZE = 1000  # tuned for small(ish) size of pub metadata


def to_es_action(es_index, line):
    d = json.loads(line)
    return {
        "_index": es_index,
        "doc": d,
    }


def clean_es(es, es_index_prefix):
    """ Ensure an empty index exists. """
    es_index = es_index_prefix + ES_INDEX
    common.clean_es(es, es_index)


def insert_file(f, es, es_index_prefix, max_items=None):
    """
    Inserts EPMC metadata from a json.gz file into Elasticsearch.

    Args:
        f: json.gz file object
        es: a living connection to elacticsearch
        max_items: maximum number of records to insert, or None
    """
    if es_index_prefix:
        es_index = es_index_prefix + ES_INDEX
    else:
        es_index = ES_INDEX

    logging.info(
        'epmc_metadata.insert_file: f=%s es=%s max_items=%s',
        f, es, max_items)
    to_es_func = functools.partial(to_es_action, es_index)
    return common.insert_actions(
        es,
        common.yield_actions(f, to_es_func, max_items),
        CHUNK_SIZE,
        )


if __name__ == '__main__':
    count = common.insert_from_argv(
        __doc__.strip(), clean_es, insert_file)
    logging.info('Imported %d pubs into ES', count)
