""" Matches manually annotated titles against EPMC for manual verification
    before use for evaluation.
"""

import datetime
from airflow import DAG
import airflow.configuration as conf
import airflow.utils.dates

from reach.airflow.tasks import fuzzy_match_refs
from reach.airflow.tasks import evaluator

DEFAULT_ARGS = {
    'depends_on_past': False,
    'start_date': airflow.utils.dates.days_ago(2),
    'retries': 0,
    'retry_delay': datetime.timedelta(minutes=5),
}


# dag.id of dag which produced the EPMC ES Index
ES_INDEX="policy"

#
# Configuration & paths
#

def verify_s3_prefix():
    reach_s3_prefix = conf.get("core", "reach_s3_prefix")
    assert reach_s3_prefix.startswith('s3://')
    assert not reach_s3_prefix.endswith('/')

# Force verification of S3 prefix on import
verify_s3_prefix()


def get_es_hosts():
    result = conf.get("core", "elasticsearch_hosts")
    assert result
    return [x.strip().split(':') for x in result.split(',')]


def from_s3_input(slug, file):
    """ Returns the S3 URL for an input fiule required by the DAG. """
    return (
        '{{ conf.get("core", "reach_s3_prefix") }}'
        '/%s/%s'
    ) % (slug, file)


def to_s3_output(dag, *args):
    """ Returns the S3 URL for any output file for the DAG. """
    components, suffix = args[:-1], args[-1]
    path = '/'.join(components)
    slug = '-'.join(components)
    return (
        '{{ conf.get("core", "reach_s3_prefix") }}'
        '/output/%s/%s%s'
    ) % (dag.dag_id, slug, suffix)


EPMC_METADATA_KEY = '/'.join([
    '{{ conf.get("core", "openresearch_s3_prefix") }}',
    'output', 'open-research', 'epmc-metadata', 'epmc-metadata.json.gz'
    ])


#
# Tasks within the DAG
#


def create_match_dag(dag_id, default_args):
    """
    Creates a DAG that produces citations using both fuzzy and exact
    matchers.

    Args:
        dag_id: dag id
        default_args: default args for the DAG
    """
    dag = DAG(
        dag_id=dag_id,
        default_args=default_args,
        schedule_interval=None
    )

    addedDocidToTitleAnnotations = evaluator.AddDocidToTitleAnnotations(
        task_id='EvaluateAddDocidToTitleAnnotations',
        refs_s3_key=from_s3_input(
            'data',
            '2019.10.8_valid.jsonl.gz',
        ),
        titles_s3_key=from_s3_input(
            'data',
            '2019.10.8_valid_TITLE.jsonl.gz',
        ),
        dst_s3_key=to_s3_output(
            dag, 'matched-annotations', '.json.gz'),
        dag=dag,
    )

    extractedGoldRefs = evaluator.ExtractRefsFromGoldDataOperator(
        task_id='EvaluateExtractRefsFromGoldData',
        src_s3_key=addedDocidToTitleAnnotations.dst_s3_key,
        dst_s3_key=to_s3_output(
            dag, 'extracted-gold-refs', '.json.gz'),
        dag=dag,
    )

    fuzzyMatchGoldRefs = fuzzy_match_refs.FuzzyMatchRefsOperator(
        task_id='EvaluateFuzzyMatchGoldRefs',
        es_hosts=get_es_hosts(),
        src_s3_key=extractedGoldRefs.dst_s3_key,
        organisation='gold',
        dst_s3_key=to_s3_output(
            dag, 'fuzzy-matched-gold-refs', '.json.gz'),
        es_index='-'.join([ES_INDEX, 'epmc', 'metadata']),
        dag=dag,
    )

    addedDocidToTitleAnnotations >> extractedGoldRefs >> fuzzyMatchGoldRefs
    return dag


matched_annotated_titles_dag = create_match_dag(
    'match_annotated_titles',
    DEFAULT_ARGS,
)

