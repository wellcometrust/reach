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
parser.add_argument('s3_url')

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


def write_to_es(es, line):
    """ Writes the given csv line to elasticsearch.

    Args:
        es: a living connection to elacticsearch
        line: a dict from a csv line. Should contain a file hash and the
              full text of a pdf
    """
    # TODO: Use real pdf titles and orgs
    # Select a random org for the time being
    orgs = ['who', 'nice', 'msf']
    org = random.choice(orgs)
    body = json.dumps({
        'hash': line['file_hash'],
        'text': line['pdf_text'],
        'title': line['pdf_name'],
        'organisation': org,
    })
    es.index(
        index='datalabs-fulltexts',
        ignore=400,
        body=body,
        doc_type='pdf_fulltext'
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
        index='datalabs-fulltexts',
        body=body,
    )


def import_data(s3_file, es, size):
    """ Import data from a given file in elasticsearch.

    Args:
        s3_file: a file object from boto3's s3
        es: a living connection to elasticsearch
        size: the size of the data to pull in bytes

    """
    with tempfile.TemporaryFile(mode='r+b') as tf:
        rows = s3_file.get(Range='bytes=0-%d' % size)
        for data in rows['Body']:
            tf.write(data)

        print('Got the fileobj')
        tf.seek(0)
        with open(tf.fileno(), mode='r', closefd=False) as csv_file:
            for line in csv.DictReader(csv_file):
                print(line['file_hash'])
                write_to_es(es, line)


if __name__ == '__main__':
    args = parser.parse_args()

    assert args.s3_url.startswith('s3://'), (
            "You must provide a valid s3:// link"
        )

    es = Elasticsearch([{'host': args.host, 'port': args.port}])
    s3 = boto3.resource('s3')

    parsed_url = urlparse(args.s3_url)
    print('Getting %s from %s bucket' % (parsed_url.path, parsed_url.netloc))
    s3_file = s3.Object(bucket_name=parsed_url.netloc, key=parsed_url.path[1:])

    # This is a big file. The size should be in megabytes, not in bytes
    size = args.size * 1000 ** 2

    # Full texts are big, so get rid of python limitation for csv field size
    csv.field_size_limit(1000000)

    if args.clean:
        clean_es(es)

    import_data(s3_file, es, size)
