""" Takes a given file size (default to 100MB) from a dataset in S3 and
import them into a running Elasticsearch database.
"""

import tempfile
import csv
import json
import random

import boto3
from urllib.parse import urlparse
from argparse import ArgumentParser
from elasticsearch import Elasticsearch

parser = ArgumentParser()
parser.add_argument('file_url')

parser.add_argument('-s', '--size',
                    default=1024,
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


def write_to_es(es, item):
    """ Writes the given csv line to elasticsearch.

    Args:
        es: a living connection to elacticsearch
        item: an dict from a json line. 
    """
    if item["sections"]:
        print(item['hash'])

        section = item['sections']['Reference']
        body = json.dumps({
            'section': section,
            'uri': item['uri'],
            'hash': item['hash']
        })  
        es.index(
            index='datalabs-sections',
            ignore=400,
            body=body,
            doc_type='section'
        )


def clean_es(es):
    """ Empty the elasticsearch database.

    Args:
        es: a living connection to elasticsearch

    """
    print('Cleaning the database..')
    body = json.dumps({
        'query': {
            'match_all': {}
        }
    })
    es.delete_by_query(
        index='datalabs-sections',
        body=body,
    )


def import_data(file_url, es, size):
    """ Import data from a given file in elasticsearch.

    Args:
        file_url: a file url
        es: a living connection to elasticsearch
        size: the size of the data to pull in bytes

    """
    def yield_from_s3(s3_url, size):
        s3 = boto3.resource('s3')
        parsed_url = urlparse(s3_url)
        print('Getting %s from %s bucket' % (parsed_url.path, parsed_url.netloc))
        s3_file = s3.Object(bucket_name=parsed_url.netloc, key=parsed_url.path[1:])
        
        with tempfile.TemporaryFile(mode='r+b') as tf:
            rows = s3_file.get(Range='bytes=0-%d' % size)
            for data in rows['Body']:
                tf.write(data)

            print('Got the fileobj')
            tf.seek(0)
            with open(tf.fileno(), mode='r', closefd=False) as json_file:
                for line in json_file:
                    yield line

    def yield_from_local(file_url, size):
        with open(file_url) as f:
            for line in f:
                yield line

    yield_lines = yield_from_s3 if file_url.startswith('s3://') else yield_from_local
    for line in yield_lines(file_url, size):
        item = json.loads(line)
        write_to_es(es, item)


if __name__ == '__main__':
    args = parser.parse_args()

    es = Elasticsearch([{'host': args.host, 'port': args.port}])

    if args.clean:
        clean_es(es)

    size = args.size * 1024 * 1000 ** 2
    import_data(args.file_url, es, size)
