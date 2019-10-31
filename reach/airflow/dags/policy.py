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

from reach.airflow.tasks.spider_operator import SpiderOperator
from reach.airflow.tasks.extract_refs_operator import ExtractRefsOperator
from reach.airflow.tasks.parse_pdf_operator import ParsePdfOperator

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

#
# Configuration & paths
#


def verify_s3_prefix():
    reach_s3_prefix = conf.get("core", "reach_s3_prefix")
    assert reach_s3_prefix.startswith('s3://')
    assert not reach_s3_prefix.endswith('/')


verify_s3_prefix()


def get_es_hosts():
    result = conf.get("core", "elasticsearch_hosts")
    assert result
    return [x.strip() for x in result.split(',')]


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


def create_org_pipeline(dag, organisation, item_limits, spider_years, epmc_metadata_key=None):
    """ Creates all tasks tied to a single organisation::

        Spider -> ParsePdf
                    \-> ExtractRefs -> FuzzyMatchRefs
                    \-> ESIndexFulltextdocs -> FullTextMatchRefs
    """
    spider = SpiderOperator(
        task_id='Spider.%s' % organisation,
        organisation=organisation,
        dst_s3_dir=to_s3_output_dir(
            dag, 'spider', organisation),
        item_years=spider_years,
        item_max=item_limits.spiders,
        dag=dag)

    parsePdf = ParsePdfOperator(
        task_id='ParsePdf.%s' % organisation,
        organisation=organisation,
        src_s3_dir=spider.dst_s3_dir,
        dst_s3_key=to_s3_output(
            dag, 'parsed-pdfs', organisation, '.json.gz'),
        dag=dag)

    esIndexFullTexts = es_index_fulltext_docs.ESIndexFulltextDocs(
        task_id="ESIndexFulltextDocs.%s" % organisation,
        src_s3_key=parsePdf.dst_s3_key,
        organisation=organisation,
        es_hosts=get_es_hosts(),
        item_limits=item_limits.index,
        es_index='-'.join([dag.dag_id, 'docs']),
        dag=dag
    )

    extractRefs = ExtractRefsOperator(
        task_id='ExtractRefs.%s' % organisation,
        src_s3_key=parsePdf.dst_s3_key,
        dst_s3_key=to_s3_output(
            dag, 'extracted-refs', organisation, '.json.gz'),
        dag=dag)

    fuzzyMatchRefs = fuzzy_match_refs.FuzzyMatchRefsOperator(
        task_id='FuzzyMatchRefs.%s' % organisation,
        es_hosts=get_es_hosts(),
        src_s3_key=extractRefs.dst_s3_key,
        dst_s3_key=to_s3_output(
            dag, 'fuzzy-matched-refs', organisation, '.json.gz'),
        es_index='-'.join([dag.dag_id, 'epmc', 'metadata']),
        dag=dag,
        )

    exactMatchRefs = exact_match_refs_operator.ExactMatchRefsOperator(
        task_id='ExactMatchRefs.%s' % organisation,
        es_hosts=get_es_hosts(),
        publications_path=epmc_metadata_key,
        exact_matched_references_path=to_s3_output(
            dag, 'exact-matched-refs', organisation, '.json.gz'),
        es_full_text_index=esIndexFullTexts,
        dag=dag)
    
    esIndexFuzzyMatched = es_index_fuzzy_matched.ESIndexFuzzyMatchedCitations(
        task_id="ESIndexFuzzyMatchedCitations.%s" % organisation,
        src_s3_key=fuzzyMatchRefs.dst_s3_key,
        organisation=organisation,
        es_hosts=get_es_hosts(),
        item_limits=item_limits.index,
        es_index='-'.join([dag.dag_id, 'citations']),
        dag=dag
    )

    parsePdf >> esIndexFullTexts >> exactMatchRefs
    spider >> parsePdf >> extractRefs >> fuzzyMatchRefs >> esIndexFuzzyMatched
    return fuzzyMatchRefs, exactMatchRefs


def create_dag(dag_id, default_args, spider_years,
               item_limits):
    """
    Creates a DAG.

    Args:
        default_args: default args for the DAG
        spider_op_cls: Spider operator class.
    """
    dag = DAG(
        dag_id=dag_id,
        default_args=default_args,
        schedule_interval='0 0 * * 0,3'
    )

    epmc_metadata_key = '/'.join([
        '{{ conf.get("core", "openresearch_s3_prefix") }}',
        'output', 'open-research', 'epmc-metadata', 'epmc-metadata.json.gz'
    ])

    esIndexPublications = es_index_epmc_metadata.ESIndexEPMCMetadata(
        task_id='ESIndexEPMCMetadata',
        src_s3_key=epmc_metadata_key,
        es_hosts=get_es_hosts(),
        max_epmc_metadata=item_limits.index,
        es_index='-'.join([dag_id, 'epmc', 'metadata']),
        dag=dag
    )
    for organisation in ORGANISATIONS:
        fuzzyMatchRefs, exactMatchRefs = create_org_pipeline(
            dag,
            organisation,
            item_limits,
            spider_years,
            epmc_metadata_key,
        )
        esIndexPublications >> fuzzyMatchRefs
        esIndexPublications >> exactMatchRefs

    return dag


test_dag = create_dag(
    'policy-test',
    DEFAULT_ARGS,
    [2018],
    ItemLimits(10, 500),
)

policy_dag = create_dag(
    'policy',
    DEFAULT_ARGS,
    list(range(2012, datetime.datetime.now().year + 1)),
    ItemLimits(None, None),
)
