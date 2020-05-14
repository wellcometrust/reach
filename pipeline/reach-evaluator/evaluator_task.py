#!/usr/bin/env python3
"""
Operators for running the end-to-end evaluation of Reach.
"""
import os
import tempfile
import logging
import json
import gzip
import argparse

from hooks import s3hook
from hooks.sentry import report_exception

# from airflow.models import BaseOperator
# from airflow.utils.decorators import apply_defaults

from reach_evaluator import ReachEvaluator

logger = logging.getLogger(__name__)

def _yield_jsonl_from_gzip(fileobj):
    """ Yield a list of dicts read from gzipped json(l)
    """
    with gzip.GzipFile(mode='rb', fileobj=fileobj) as f:
        for line in f:
            yield json.loads(line)

def _yield_jsonl(fileobj):
    """ Yield a list of dicts read from gzipped json(l)
    """
    for line in fileobj:
        yield json.loads(line)

def _get_span_text(text, span):
    """Get the text that is demarcated by a span in a prodigy dict
    """
    return text[span['start']:span['end']]

def _write_json_gz_to_s3(s3, data, key):
    """Write a list of jsons to json.gz on s3
    """
    with tempfile.NamedTemporaryFile(mode='wb') as output_raw_f:
        with gzip.GzipFile(mode='wb', fileobj=output_raw_f) as output_f:
            for item in data:
                output_f.write(json.dumps(item).encode('utf-8'))
                output_f.write(b'\n')

        output_raw_f.flush()
        s3.load_file(
            filename=output_raw_f.name,
            dst_key=key
        )

def _read_json_gz_from_s3(s3, key):
    """Write a list of jsons to json.gz on s3
    """
    with tempfile.TemporaryFile(mode='rb+') as tf:
        key = s3.get_s3_object(key)
        key.download_fileobj(tf)
        tf.seek(0)

        return list(_yield_jsonl_from_gzip(tf))

def _read_jsonl_from_s3(s3, key):
    """Write a list of jsons to json.gz on s3
    """
    with tempfile.TemporaryFile(mode='rb+') as tf:
        key = s3.get_s3_object(key)
        key.download_fileobj(tf)
        tf.seek(0)

        return list(_yield_jsonl(tf))

class EvaluateOperator(object):
    """
    Take the output of fuzz-matched-refs operator and evaluates the results
    against a manually labelled gold dataset, returning results in a json
    to s3.

    Args:
        src_s3_key: S3 URL for input
        dst_s3_key: S3 URL for output
    """

    template_fields = (
        'gold_s3_key',
        'reach_s3_key',
        'dst_s3_key',
    )

    def __init__(self, gold_s3_key, reach_s3_key, dst_s3_key, reach_params=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gold_s3_key = gold_s3_key
        self.reach_s3_key = reach_s3_key
        self.dst_s3_key = dst_s3_key
        self.reach_params = reach_params

    @report_exception
    def execute(self):

        s3 = s3hook.S3Hook()

        results = []

        # Read data from S3
        gold = _read_jsonl_from_s3(s3, self.gold_s3_key)
        reach = _read_json_gz_from_s3(s3, self.reach_s3_key)

        evaluator = ReachEvaluator(gold, reach)
        eval_results = evaluator.eval()

        # Add additional metadata

        eval_results['gold_refs'] = self.gold_s3_key
        eval_results['reach_refs'] = self.reach_s3_key
        eval_results['reach_params'] = self.reach_params

        # Write the results to S3
        _write_json_gz_to_s3(s3, [eval_results], key=self.dst_s3_key)

        logger.info(
            'EvaluateOperator: Finished Evaluating Reach matches'
        )


if __name__ == '__main__':

    arg_parser = argparse.ArgumentParser(
        description='Evaluates how well the algorithm has performed given some'
                    ' gold standard data and writes the'
                    ' results to the given S3 path.'
    )
    arg_parser.add_argument(
        'gold_s3_key',
        help='The gold annotation path in s3.'
    )
    arg_parser.add_argument(
        'src_s3_key',
        help='The source path to s3.'
    )
    arg_parser.add_argument(
        'dst_s3_key',
        help='The destination path to s3.'
    )
    
    args = arg_parser.parse_args()

    evaluateRefs = EvaluateOperator(
        gold_s3_key=args.gold_s3_key,
        reach_s3_key=args.src_s3_key,
        dst_s3_key=args.dst_s3_key,
        )
    evaluateRefs.execute()

