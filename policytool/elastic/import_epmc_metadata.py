""" Takes a given publication metadata number (default to 500) from a dataset
in S3 and import them into a running Elasticsearch database.
"""

import json
import gzip

import boto3
from urllib.parse import urlparse
from argparse import ArgumentParser
from elasticsearch import Elasticsearch

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

parser.add_argument('-P', '--port',
                    default='9200',
                    help='Port of the Elasticsearch server')


def yield_publications_metadata(json_archive):
    """ Given a gzip streaming body, yield a publication as a dict.

    Args:
        json_archive: An open gzip file as a streaming body from s3

    Yields:
        publication: A dict describing a publication from EPMC
    """
    with gzip.GzipFile(fileobj=json_archive, mode='r') as json_file:

        for line in json_file:
            yield json.loads(line)


def write_to_es(es, line):
    """ Writes the given csv line to elasticsearch.

    Args:
        es: a living connection to elacticsearch
        line: a dict from a csv line. Should contain a file hash and the
              full text of a pdf
    """
    body = json.dumps(line)
    es.index(
        index='epmc-metadata',
        ignore=400,
        body=body,
        doc_type='publication-metadata'
    )


def import_into_elasticsearch(s3_file, es, max_publication=10):
    """ Read publications from the given s3 file and write them to the
    elasticsearch database.

    Args:
        es: a living connection to elacticsearch
        s3_file: An open StreamingBody from s3
    """
    for index, publication in enumerate(
        yield_publications_metadata(s3_file.get()['Body'])
    ):
        if max_publication > 0 and index >= max_publication:
            break
        write_to_es(es, publication)


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

    import_into_elasticsearch(s3_file, es)
