"""
Inserts fulltext documents (policy docs, normally) into Elasticsearch.

Sample URL for testing:

    s3://datalabs-dev/reach-airflow/output/test_dag/policy-parse/nice/policy-parse-nice.json.gz
"""

import functools
import json
import logging


from . import common

CHUNK_SIZE = 50  # tuned for large(ish) size of policy docs


def to_es_action(org, es_index, line):
    """ Returns a preformated line to add to an Elasticsearch bulk query. """
    d = json.loads(line)
    return {
        "_index": es_index,
        "doc": {
            'hash': d.get('file_hash', None),
            'text': d.get('text', None),
            'organisation': org,
            'title': d.get('title', None),
            'authors': d.get("authors", None),
            'created': d.get('created', None),
            'year': d.get('year', None),
            'source_page': d.get('source_page', None),
            'url': d.get('url', None)
        }
    }


def clean_es(es, es_index, org):
    """ Ensure an empty index exists and has a mapping.
    Delete documents from the organisation to ensure no duplicates
    are inserted.
    """
    current_mapping = common.check_mapping(es, es_index)
    if current_mapping:
        org_mapping = current_mapping[es_index][
            'mappings']['properties']['doc']['properties']['organisation']

        if org_mapping.get('type') == 'keyword':
            common.clear_index_by_org(es, org, es_index)

    mapping_body = {
        "mappings": {
            "properties": {
                "doc.text": {"type": "text"},
                "doc.organisation": {"type": "keyword"}
            }
        }
    }
    common.recreate_index(es, es_index, mapping_body)


def insert_file(f, es, org, es_index, max_items=None):
    """
    Inserts the policy documents' fulltexts from a json.gz file
    into Elasticsearch.

    Args:
        f: json.gz file object
        es: a living connection to elacticsearch
        org: organization name associated with the doc
        max_items: maximum number of records to insert, or None
    """

    logging.info(
        'fulltext_docs.insert_file: f=%s es=%s max_items=%s',
        f, es, max_items)
    to_es_func = functools.partial(to_es_action, org, es_index)
    return common.insert_actions(
        es,
        common.yield_actions(f, to_es_func, max_items),
        CHUNK_SIZE,
        )


if __name__ == '__main__':
    def insert_func(f, es, max_items=None):
        return insert_file(f, es, 'unknown', 'policy-test-fulltexts',
                           max_items=max_items)

    count = common.insert_from_argv(
        __doc__.strip(), clean_es, insert_func)

    logging.info('Imported %d pubs into ES', count)
