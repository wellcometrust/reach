import datetime
import os
from collections import namedtuple
from airflow import DAG
import airflow.configuration as conf
import airflow.utils.dates

from policytool.airflow.tasks import es_index_epmc_metadata
from policytool.airflow.tasks import es_index_fulltext_docs
from policytool.airflow.tasks.spider_operator import SpiderOperator
from policytool.airflow.tasks.extract_refs_operator import ExtractRefsOperator
from policytool.airflow.tasks.parse_pdf_operator import ParsePdfOperator

ORGANISATIONS = [
    'who_iris',
    'nice',
    'gov_uk',
    'msf',
    'unicef',
    'parliament',
]

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


verify_s3_prefix()


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


def to_s3_model(*args):
    """ Returns the S3 URL for to a model, rooted under
    ${REACH_S3_PREFIX}/models/"""
    return (
        '{{ conf.get("core", "reach_s3_prefix") }}'
        '/models/%s'
    ) % '/'.join(args)


def create_extract_pipeline(dag, organisation,
                            item_limits, spider_years):

    spider = SpiderOperator(
        task_id='Spider.%s' % organisation,
        organisation=organisation,
        dst_s3_dir=to_s3_output_dir(
            dag, 'policy-scrape', organisation),
        item_years=spider_years,
        item_max=item_limits.spiders,
        dag=dag)

    s3_parse_dst_key = to_s3_output(
            dag, 'policy-parse', organisation, '.json.gz')

    parsePdfs = ParsePdfOperator(
        task_id='ParsePdf.%s' % organisation,
        organisation=organisation,
        src_s3_dir=spider.dst_s3_dir,
        dst_s3_key=s3_parse_dst_key,
        dag=dag)

    es_index_fulltexts = es_index_fulltext_docs.ESIndexFulltextDocs(
        task_id="ESIndexFulltextDocs.%s" % organisation,
        src_s3_key=s3_parse_dst_key,
        organisation=organisation,
        es_host='elasticsearch',
        item_limits=item_limits.index,
        dag=dag
    )

    parser_model = to_s3_model(
        'reference_parser_models',
        'reference_parser_pipeline.pkl')

    extractRefs = ExtractRefsOperator(
        task_id='ExtractRefs.%s' % organisation,
        model_path=parser_model,
        src_s3_key=parsePdfs.dst_s3_key,
        dst_s3_key=to_s3_output(
            dag, 'policy-extract', organisation, '.json.gz'),
        dag=dag)

    parsePdfs >> es_index_fulltexts
    spider >> parsePdfs >> extractRefs
    return extractRefs


def create_dag(dag_id, default_args, spider_years, item_limits):
    """
    Creates a DAG.

    Args:
        default_args: default args for the DAG
        spider_op_cls: Spider operator class.
    """
    dag = DAG(
        dag_id=dag_id,
        default_args=default_args,
        schedule_interval='0 0 * * 0'
    )

    epmc_metadata_key = '/'.join([
        '{{ conf.get("core", "openresearch_s3_prefix") }}',
        'output', 'open-research', 'epmc-metadata', 'epmc-metadata.json.gz'
    ])

    es_index_publications = es_index_epmc_metadata.ESIndexEPMCMetadata(
        task_id='ESIndexEPMCMetadata',
        src_s3_key=epmc_metadata_key,
        es_host='elasticsearch',
        max_epmc_metadata=item_limits.index,
        dag=dag
    )
    for organisation in ORGANISATIONS:
        extract_task = create_extract_pipeline(
            dag,
            organisation,
            item_limits,
            spider_years,
        )

    return dag


test_dag = create_dag(
    'test_dag',
    DEFAULT_ARGS,
    [2018],
    ItemLimits(10, 500),
)

policy_dag = create_dag(
    'policy_dag',
    DEFAULT_ARGS,
    list(range(2012, datetime.datetime.now().year + 1)),
    ItemLimits(None, None),
)
