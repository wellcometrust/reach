""" Takes a given publication metadata number (default to 500) from a dataset
in S3 and import them into a running Elasticsearch database.
"""

import tempfile
import logging
import gzip
from functools import partial
from urllib.parse import urlparse
from argparse import ArgumentParser
from multiprocessing.dummy import Pool as ThreadPool

import boto3
from elasticsearch import Elasticsearch

logger = logging.getLogger(__name__)
es_logger = logging.getLogger('elasticsearch')
es_logger.setLevel(logging.WARNING)
logger.setLevel(logging.INFO)

THREADPOOL_SIZE = 6
EPMC_METADATA_INDEX = 'epmc-metadata'
CHUNCK_SIZE = 1000

parser = ArgumentParser()
parser.add_argument('s3_url')

parser.add_argument('-n', '--publication-number',
                    default=500,
                    type=int,
                    help=('The number of publicatios to pull. Defaults to 500.'
                          'A negative value will pull the entire dataset'))

parser.add_argument('-H', '--host',
                    default='127.0.0.1',
                    help='Address of the Elasticsearch server')

parser.add_argument('-C', '--clean', dest='clean', action='store_true',
                    help='Clean the elasticsearch database before import')

parser.add_argument('-P', '--port',
                    default='9200',
                    help='Port of the Elasticsearch server')


def build_es_bulk(line):
    """ Returns a preformated line to add to an Elasticsearch bulk query. """
    action = '{"index": {"_index": "%s"}}' % EPMC_METADATA_INDEX
    data = line + '\n'
    return '\n'.join([action, data])


def yield_publications_metadata(s3_object):
    """ Given a gzip streaming body, yield a publication as a dict.

    Args:
        json_archive: An open gzip file as a streaming body from s3

    Yields:
        publication: A dict describing a publication from EPMC
    """
    with tempfile.NamedTemporaryFile() as tf:
        s3_object.download_fileobj(tf)
        tf.seek(0)
        logger.info('Start yielding...')
        with gzip.GzipFile(fileobj=tf, mode='r') as json_file:
            for index, line in enumerate(json_file):
                yield build_es_bulk(line.decode('utf-8'))


def yield_metadata_chunk(s3_object, max_epmc_metadata, chunk_size=500):
    """ Yield bulk insertion preformatted publication list of
    chunk_size length.

    Args:
        s3_object: An s3 file object from boto
        max_epmc_metadata: The maximum number of publications to be yielded
        chunck_size: The size of the publication lists to be yielded

    Yield:
        pub_list: A list containing both actions and data to be executed by
                  Elasticsearch's bulk API
    """
    pub_list = []
    for index, metadata in enumerate(yield_publications_metadata(s3_object)):
        pub_list.append(metadata)
        if max_epmc_metadata and index + 1 >= max_epmc_metadata:
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
    logger.info(bulk_response)
    # Half of the pub list is instructions
    return len(pub_list) / 2


def clean_es(es):
    """ Empty the elasticsearch database.

    Args:
        es: a living connection to elasticsearch

    """
    logger.info('Cleaning the database..')
    # Ignore if the index doesn't exist, as it'll be created by next queries
    es.indices.delete(
        index=EPMC_METADATA_INDEX,
        ignore=[404]
    )


def import_into_elasticsearch(s3_file, es, max_epmc_metadata=1000):
    """ Read publications from the given s3 file and write them to the
    elasticsearch database.

    Args:
        es: a living connection to elacticsearch
        s3_file: An open StreamingBody from s3
        max_epmc_metadata: The maximum publication number to be inserted
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
                s3_file,
                chunk_size=CHUNCK_SIZE,
                max_epmc_metadata=max_epmc_metadata,
            )
        ):
            insert_sum += line_count
    return es.count(index=EPMC_METADATA_INDEX), insert_sum


if __name__ == '__main__':
    args = parser.parse_args()

    assert args.s3_url.startswith('s3://'), (
            "You must provide a valid s3:// link"
        )

    es = Elasticsearch(
        [{'host': args.host, 'port': args.port}],
        retry_on_timeout=True,
        max_retry=10,
    )
    s3 = boto3.resource('s3')

    if args.clean:
        clean_es(es)

    parsed_url = urlparse(args.s3_url)
    logger.info('Getting %s from %s bucket' % (
        parsed_url.path,
        parsed_url.netloc
    ))
    s3_file = s3.Object(
        bucket_name=parsed_url.netloc,
        key=parsed_url.path[1:]
    )
    if args.publication_number < 0:
        res = import_into_elasticsearch(s3_file, es, None)
    else:
        res = import_into_elasticsearch(s3_file, es, args.publication_number)

    logger.info('Imported %d pubs into ES', res['count'])