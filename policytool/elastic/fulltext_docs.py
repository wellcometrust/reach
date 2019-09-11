"""
Inserts fulltext documents (policy docs, normally) into Elasticsearch.

Sample URL for testing:

    s3://datalabs-dev/reach-airflow/output/test_dag/policy-parse/nice/policy-parse-nice.json.gz
"""

import functools
import json
import logging

from . import common

ES_INDEX = 'datalabs-fulltext'
CHUNK_SIZE = 50  # tuned for large(ish) size of policy docs

def to_es_action(org, line):
    """ Returns a preformated line to add to an Elasticsearch bulk query. """
    d = json.loads(line)
    return {
        "_index": ES_INDEX,
        "doc": {
            'hash': d['file_hash'],
            'text': d['text'],
            'organisation': org,
        }
    }


def clean_es(es):
    """ Ensure an empty index exists. """
    common.clean_es(es, ES_INDEX)


def insert_file(f, es, org, max_items=None):
    """
    Inserts EPMC metadata from a json.gz file into Elasticsearch.

    Args:
        f: json.gz file object
        es: a living connection to elacticsearch
        org: organization name associated with the doc
        max_items: maximum number of records to insert, or None
    """

    logging.info(
        'fulltext_docs.insert_file: f=%s es=%s max_items=%s',
        f, es, max_items)
    to_es_func = functools.partial(to_es_action, org)
    return common.insert_actions(
        es,
        common.yield_actions(f, to_es_func, max_items),
        CHUNK_SIZE,
        )


if __name__ == '__main__':
    def insert_func(f, es, max_items=None):
        return insert_file(f, es, 'unknown', max_items=max_items)

    count = common.insert_from_argv(
        __doc__.strip(), clean_es, insert_func)

    logging.info('Imported %d pubs into ES', count)
