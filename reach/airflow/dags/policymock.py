import datetime
import os
from collections import namedtuple
from airflow import DAG
import airflow.configuration as conf
import airflow.utils.dates

from reach.airflow.tasks import es_index_epmc_metadata
from reach.airflow.tasks import es_index_fulltext_docs
from reach.airflow.tasks import es_index_fuzzy_matched
from reach.airflow.tasks import exact_match_refs_operator
from reach.airflow.tasks import fuzzy_match_refs
from reach.airflow.tasks import policy_name_normalizer

from reach.airflow.tasks.spider_operator import SpiderOperator
from reach.airflow.tasks.extract_refs_operator import ExtractRefsOperator
from reach.airflow.tasks.parse_pdf_operator import ParsePdfOperator


DEFAULT_ARGS = {
    'depends_on_past': False,
    'start_date': airflow.utils.dates.days_ago(2),
    'retries': 0,
    'retry_delay': datetime.timedelta(minutes=5),
}

ItemLimits = namedtuple('ItemLimits', ('spiders', 'index'))

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


def to_s3_output(dag, *args):
    """ Returns the S3 URL for any output file for the DAG. """
    components, suffix = args[:-1], args[-1]
    path = '/'.join(components)
    slug = '-'.join(components)
    return (
        '{{ conf.get("core", "reach_s3_prefix") }}'
        '/output/%s/%s/%s%s'
    ) % (dag.dag_id, path, slug, suffix)


def to_s3_output_dir(dag, *args):
    """ Returns the S3 URL for any output directory for the DAG. """
    path = '/'.join(args)
    slug = '-'.join(args)
    return (
        '{{ conf.get("core", "reach_s3_prefix") }}'
        '/output/%s/%s/%s'
    ) % (dag.dag_id, path, slug)


"""
EPMC_METADATA_KEY = '/'.join([
    '{{ conf.get("core", "openresearch_s3_prefix") }}',
    'output', 'open-research', 'epmc-metadata', 'epmc-metadata.json.gz'
    ])
"""
EPMC_METADATA_KEY = "file://Users/jdu/Projects/wellcome/data/epmc-metadata.json.gz"



def create_e2e_test(dag_id, default_args, spider_years, item_limits):
    """ Creates a simple dag for testing end to end functionality """

    dag = DAG(
        dag_id=dag_id,
        default_args=default_args,
        schedule_interval=("0 0 * * 0,3"),
    )

    spider = SpiderOperator(
        task_id="Spider.acme",
        organisation="acme",
        dst_s3_dir=to_s3_output_dir(
            dag, "spider", "acme_inc"
        ),
        item_years=spider_years,
        item_max=item_limits.spiders,
        dag=dag
    )

    parsePdf = ParsePdfOperator(
        task_id="ParsePdf.acme",
        organisation="acme",
        src_s3_dir=spider.dst_s3_dir,
        dst_s3_key=to_s3_output(
            dag, 'parsed-pdfs', 'acme', '.json.gz'),
        dag=dag
    )

    name_normalizer = policy_name_normalizer.PolicyNameNormalizerOperator(
        task_id="NameNormalisation.acme",
        organisation="acme",
        src_s3_key=parsePdf.dst_s3_key,
        dst_s3_key=to_s3_output(dag, 'normalized-names', 'acme', '.json.gz'),
        dag=dag
    )

    esIndexFullTexts = es_index_fulltext_docs.ESIndexFulltextDocs(
        task_id="ESIndexFulltextDocs.acme",
        src_s3_key=name_normalizer.dst_s3_key,
        organisation='acme',
        es_hosts=get_es_hosts(),
        item_limits=item_limits.index,
        es_index='-'.join([dag.dag_id, 'docs']),
        dag=dag
    )

    extractRefs = ExtractRefsOperator(
        task_id='ExtractRefs.acme',
        src_s3_key=name_normalizer.dst_s3_key,
        split_s3_key=to_s3_output(
            dag, 'split-refs', 'acme', '.json.gz'),
        parsed_s3_key=to_s3_output(
            dag, 'extracted-refs', 'acme', '.json.gz'),
        dag=dag
    )

    epmc_data = es_index_epmc_metadata.ESIndexEPMCMetadata(
        task_id='ESIndexEPMCMetadata',
        src_s3_key=EPMC_METADATA_KEY,
        es_hosts=get_es_hosts(),
        max_epmc_metadata=item_limits.index,
        es_index='-'.join([dag.dag_id, 'epmc', 'metadata']),
        dag=dag
    )

    fuzzyMatchRefs = fuzzy_match_refs.FuzzyMatchRefsOperator(
        task_id='FuzzyMatchRefs.acme',
        es_hosts=get_es_hosts(),
        src_s3_key=extractRefs.parsed_s3_key,
        organisation="acme",
        dst_s3_key=to_s3_output(
            dag, 'fuzzy-matched-refs', 'acme', '.json.gz'),
        es_index='-'.join([dag.dag_id, 'epmc', 'metadata']),
        dag=dag,
    )

    esIndexFuzzyMatched = es_index_fuzzy_matched.ESIndexFuzzyMatchedCitations(
        task_id="ESIndexFuzzyMatchedCitations.acme",
        src_s3_key=fuzzyMatchRefs.dst_s3_key,
        organisation='acme',
        es_hosts=get_es_hosts(),
        item_limits=item_limits.index,
        es_index='-'.join([dag.dag_id, 'citations']),
        dag=dag
    )

    epmc_data >> fuzzyMatchRefs
    spider >> parsePdf >> name_normalizer >> esIndexFullTexts
    name_normalizer >> extractRefs >> fuzzyMatchRefs >> esIndexFuzzyMatched
    return dag


# TODO: Put this behind a DEBUG flag
policymock_dag = create_e2e_test(
    'policy-mock',
    DEFAULT_ARGS,
    [2018],
    ItemLimits(None, None),
)
