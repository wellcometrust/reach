import datetime
import os
from airflow import DAG
import airflow.configuration as conf
import airflow.utils.dates

from policytool.airflow.tasks.dummy_spider_operator import DummySpiderOperator
from policytool.airflow.tasks.run_spider_operator import RunSpiderOperator
from policytool.airflow.tasks.extract_refs_operator import ExtractRefsOperator
from policytool.airflow.tasks.parse_pdf_operator import ParsePdfOperator
from policytool.airflow.tasks.es_index_publications import ESIndexPublications
from policytool.airflow.tasks.es_index_fulltext import ESIndexFulltexts


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
                            spider_op_cls, es_index_publications):
    spider = spider_op_cls(
        task_id='Spider.%s' % organisation,
        organisation=organisation,
        dst_s3_dir=to_s3_output_dir(
            dag, 'policy-scrape', organisation),
        dag=dag)

    s3_parse_dst_key = to_s3_output(
            dag, 'policy-parse', organisation, '.json.gz')

    parsePdfs = ParsePdfOperator(
        task_id='ParsePdf.%s' % organisation,
        organisation=organisation,
        src_s3_dir=spider.dst_s3_dir,
        dst_s3_key=s3_parse_dst_key,
        dag=dag)

    es_index_fulltexts = ESIndexFulltexts(
        task_id="ESIndexFulltexts.%s" % organisation,
        src_s3_key=s3_parse_dst_key,
        organisation=organisation,
        es_host='elasticsearch',
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

    es_index_fulltexts << parsePdfs
    es_index_publications >> spider >> parsePdfs >> extractRefs
    return extractRefs


def create_dag(default_args, spider_op_cls):
    """
    Creates a DAG.

    Args:
        default_args: default args for the DAG
        spider_op_cls: Spider operator class, i.e. RunSpiderOperator or
            DummySpiderOperator.
    """
    dag = DAG(
        dag_id='test_dag',
        default_args=default_args,
        schedule_interval='0 0 * * 0'
    )

    epmc_metadata_key = '/'.join([
        '{{ conf.get("core", "openresearch_s3_prefix") }}',
        'output', 'open-research', 'epmc-metadata', 'epmc-metadata.json.gz'
    ])

    es_index_publications = ESIndexPublications(
        task_id=ESIndexPublications.__name__,
        src_s3_key=epmc_metadata_key,
        es_host='elasticsearch',
        dag=dag
    )
    for organisation in ORGANISATIONS:
        create_extract_pipeline(
            dag,
            organisation,
            spider_op_cls,
            es_index_publications
        )

    return dag


test_dag = create_dag(DEFAULT_ARGS, DummySpiderOperator)
