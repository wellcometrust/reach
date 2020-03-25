"""
Operator to run to index files from a given S3 location to a running
Elasticsearch instance.
"""
import os
import tempfile
import argparse

from hooks.s3hook import S3Hook, ORGS
from elastic import fulltext_docs, epmc_metadata, fuzzy_matched_citations

import elastic.common


INDEX_METHODS = {
    'epmc': epmc_metadata,
    'fulltexts': fulltext_docs,
    'citations': fuzzy_matched_citations,
}


class ESIndex(object):
    """ Download an idexable json.gz file from S3 and index
    them with Elasticsearch.
    """

    def __init__(self, src_s3_key, es_hosts, organisation, es_port=9200,
                 es_index=None, max_items=None):
        """
        Args:
            src_s3_key: S3 URL for the json.gz output file.
            es_hosts: the hostname of elasticsearch database.
            es_port: the port of elasticsearch database. Default to 9200.
            max_items: Maximum number of fulltexts to process.
            es_index: The index to insert data to
        """

        if not src_s3_key.endswith('.json.gz'):
            raise ValueError('src_s3_key must end in .json.gz')

        self.src_s3_key = src_s3_key
        self.es_hosts = es_hosts
        self.es_port = es_port
        self.organisation = organisation
        self.max_items = max_items
        self.es_index = es_index

    def execute(self, index_method):
        es = elastic.common.connect(self.es_hosts)
        s3 = S3Hook()

        # TODO: implement skipping mechanism
        index_method.clean_es(es, self.es_index, self.organisation)

        if self.max_items:
            self.log.info(
                'Getting %s pubs from %s',
                self.max_items,
                self.src_s3_key,
            )
        else:
            self.log.info(
                'Getting %s pubs from %s',
                'all',
                self.src_s3_key,
            )

        s3_object = s3.get_key(self.src_s3_key)
        with tempfile.NamedTemporaryFile() as tf:
            s3_object.download_fileobj(tf)
            tf.seek(0)
            count = index_method.insert_file(
                tf,
                es,
                self.es_index,
                self.organisation,
                max_items=self.max_items,
            )
        self.log.info('import complete count=%d', count)


if __name__ == '__main__':
    es_host = os.environ['ES_HOST']
    es_port = os.environ.get('ES_PORT', 9200)

    arg_parser = argparse.ArgumentParser(
        description='Run a web scraper for a given organisation and writes the'
                    ' results to the given S3 path.'
    )
    arg_parser.add_argument(
        'src_s3_key',
        help='The source path to s3.'
    )
    arg_parser.add_argument(
        'organisation',
        choices=ORGS,
        default=None,
        help='The organisation to scrape.'
    )
    arg_parser.add_argument(
        'index_method',
        choices=INDEX_METHODS.keys(),
        help='The type of data to index.'
    )
    arg_parser.add_parameter(
        'max_items',
        default=None,
        help="The maximum number of items to index."
    )

    args = arg_parser.parse_args()

    es_index_name = "reach-{index}{is_test}".format(
        index=args.index_method,
        is_test="-test" if args.max_items else "",
    )

    indexer = ESIndex(
        args.src_s3_key,
        es_host,
        args.organisation,
        es_port,
        es_index_name,
        args.max_items,
    )

    indexer.execute()
