"""
Inserts fuzzy-matched citations into Elasticsearch.

Sample URL for testing:

    s3://datalabs-staging/reach-airflow/output/policy-test/fuzzy-matched-refs/nice/fuzzy-matched-refs-nice.json.gz
"""

import functools
import json
import logging

from . import common

CHUNK_SIZE = 1000  # Tuned for small citation metadata


def to_es_action(org, es_index, line):
    """ Returns a preformated line to add to an Elasticsearch bulk query. """
    d = json.loads(line)

    return {
        "_index": es_index,
        "doc": {
            'Document id': d['Document id'],
            'Reference id': d['Reference id'],
            'Extracted title': d['Extracted title'],
            'Matched title': d['Matched title'],
            'Similarity': d['Similarity'],
            'Match algorithm': d['Match algorithm'],
        }
    }


def clean_es(es, es_index, org):
    """ Ensure an empty index exists and delete documents from the
    organisation to ensure no duplicates are inserted.
    """
    es_body = {
        'query': {
            'match': {
                'organisation': org,
            }
        }
    }
    es.delete_by_query(
        index=es_index,
        body=es_body,
        ignore=[404],
    )


def insert_file(f, es, org, es_index, max_items=None):
    """
    Inserts fuzzy matched citations from a json.gz file into Elasticsearch.

    Args:
        f: json.gz file object
        es: a living connection to elacticsearch
        org: organization name associated with the doc
        max_items: maximum number of records to insert, or None
    """

    logging.info(
        'fuzzymatched_citations.insert_file: f=%s es=%s max_items=%s',
        f, es, max_items)
    to_es_func = functools.partial(to_es_action, org, es_index)
    return common.insert_actions(
        es,
        common.yield_actions(f, to_es_func, max_items),
        CHUNK_SIZE,
        )


if __name__ == '__main__':
    def insert_func(f, es, max_items=None):
        return insert_file(f, es, 'unknown', 'policy-test-fuzzymatched',
                           max_items=max_items)

    count = common.insert_from_argv(
        __doc__.strip(), clean_es, insert_func)

    logging.info('Imported %d pubs into ES', count)
