""" Takes a given number of publication fulltexts from a dataset in S3 and
import them into a running Elasticsearch database.
"""

import tempfile
import json
import gzip
import logging
from multiprocessing.dummy import Pool as ThreadPool
from functools import partial
from urllib.parse import urlparse
from argparse import ArgumentParser

import boto3
from elasticsearch import Elasticsearch

logging.basicConfig()
logger = logging.getLogger(__name__)
es_logger = logging.getLogger('elasticsearch')
es_logger.setLevel(logging.INFO)
logger.setLevel(logging.INFO)

THREADPOOL_SIZE = 6
ES_INDEX = 'datalabs-fulltext'
CHUNCK_SIZE = 1000

parser = ArgumentParser()
parser.add_argument('s3_url')
parser.add_argument('organisation')

parser.add_argument('-n', '--publication-number',
                    default=500,
                    type=int,
                    help=('The megabytes to pull. Defaults to 100.'
                          'A negative value will pull the entire dataset'))

parser.add_argument('-H', '--host',
                    default='127.0.0.1',
                    help='Address of the Elasticsearch server')

parser.add_argument('-P', '--port',
                    default='9200',
                    help='Port of the Elasticsearch server')

parser.add_argument('-C', '--clean', dest='clean', action='store_true',
                    help='Clean the elasticsearch database before import')


class IndexingErrorException(Exception):
    """Exception to raise if any error happens during elasticsearch
       bulk indexing.
    """
    pass


def build_es_bulk(line, org):
    """ Returns a preformated line to add to an Elasticsearch bulk query. """
    action = '{"index": {"_index": "%s"}}' % ES_INDEX
    line = json.loads(line)
    body = json.dumps({
        'hash': line['file_hash'],
        'text': line['text'],
        'organisation': org,
    })

    data = body + '\n'
    return '\n'.join([action, data])


def yield_publications(tf, org):
    """ Given a gzip streaming body, yield a publication as a dict.

    Args:
        json_archive: An open gzip file as a streaming body from s3

    Yields:
        publication: A dict containing the fulltext of a scraped publication
    """
    logger.info('Start yielding...')
    with gzip.GzipFile(fileobj=tf, mode='r') as json_file:
        for index, line in enumerate(json_file):
            yield build_es_bulk(line.decode('utf-8'), org)


def yield_metadata_chunk(tf, max_publication_number,
                         org, chunk_size=500):
    """ Yield bulk insertion preformatted publication list of
    chunk_size length.

    Args:
        s3_object: An s3 file object from boto
        max_publication_number: The maximum number of publications
                                to be yielded
        chunck_size: The size of the publication lists to be yielded

    Yield:
        pub_list: A list containing both actions and data to be executed by
                  Elasticsearch's bulk API
    """
    pub_list = []
    for index, metadata in enumerate(yield_publications(tf, org)):
        pub_list.append(metadata)
        if max_publication_number and index + 1 >= max_publication_number:
            yield pub_list
            pub_list = []
            return

        if len(pub_list) >= chunk_size:
            yield pub_list
            pub_list = []
    if pub_list:
        yield pub_list


def process_es_bulk(pub_list, es):
    """ Writes the given csv line to elasticsearch.

    Args:
        es: a living connection to elacticsearch
        bulk_query: a formatted bulk query to submit to Elasticsearch.
    """
    bulk_response = es.bulk(
        body=''.join(pub_list),
        refresh='wait_for',
        request_timeout=3600,
    )
    if bulk_response.get('errors'):
        logger.error('failed on bulk indexing:\n%s',
                     bulk_response)
        raise IndexingErrorException()
    return len(pub_list)


def clean_es(es):
    """ Empty the elasticsearch database.

    Args:
        es: a living connection to elasticsearch
    """
    logger.info('Cleaning the database..')
    # Ignore if the index doesn't exist, as it'll be created by next queries
    es.indices.delete(
        index=ES_INDEX,
        ignore=[404]
    )
    es.indices.create(
        index=ES_INDEX
    )


def import_into_elasticsearch(tf, es, org, max_publication_number=1000):
    """ Read publications from the given s3 file and write them to the
    elasticsearch database.

    Args:
        es: a living connection to elacticsearch
        s3_file: An open StreamingBody from s3
        max_publication_number: The maximum publication number to be inserted
    """

    insert_sum = 0
    with ThreadPool(THREADPOOL_SIZE) as pool:
        if THREADPOOL_SIZE > 1:
            pool_map = pool.imap
        else:
            pool_map = map
        for line_count in pool_map(
            partial(
                process_es_bulk,
                es=es,
            ),
            yield_metadata_chunk(
                tf,
                org=org,
                chunk_size=CHUNCK_SIZE,
                max_publication_number=max_publication_number,
            )
        ):
            insert_sum += line_count
    return es.count(index=ES_INDEX)['count'], insert_sum


if __name__ == '__main__':
    args = parser.parse_args()

    assert args.s3_url.startswith('s3://'), (
            "You must provide a valid s3:// link"
        )

    es = Elasticsearch([{'host': args.host, 'port': args.port}])
    s3 = boto3.resource('s3')

    parsed_url = urlparse(args.s3_url)
    logger.info(
        'Getting %s from %s bucket',
        parsed_url.path,
        parsed_url.netloc
    )

    if args.clean:
        clean_es(es)

    s3_object = s3.Object(
        bucket_name=parsed_url.netloc,
        key=parsed_url.path[1:]
    )
    with tempfile.NamedTemporaryFile() as tf:
        s3_object.download_fileobj(tf)
        tf.seek(0)

        total, recent = import_into_elasticsearch(
            tf,
            es,
            args.organisation,
            args.publication_number
        )
    logger.info(
        'total index publications: %d (%d recent)',
        total,
        recent,
    )
