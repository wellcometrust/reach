import os
import datetime

import airflow.utils.dates
from airflow import DAG

from policytool.airflow.tasks.es_index_publications import ESIndexPublications
from policytool.airflow.tasks.exact_match_refs_operator import (
    ExactMatchRefsOperator
)
# from policytool.airflow.tasks.fuzzy_match_refs_operator import (
#     FuzzyMatchRefsOperator
# )

MIN_TITLE_LENGTH = 40
SHOULD_MATCH_THRESHOLD = 80
SCORE_THRESHOLD = 50


args = {
    'depends_on_past': False,
    'start_date': airflow.utils.dates.days_ago(2),
    'retries': 0,  # XXX
    'retry_delay': datetime.timedelta(minutes=5),
}

dag = DAG(
    dag_id='test_dag',
    default_args=args,
    schedule_interval='0 0 * * 0'
)


epmc_metadata_key = '/'.join([
    '{{ conf.get("core", "datalabs_s3_prefix") }}',
    'output', 'open-research', 'epmc-metadata', 'epmc-metadata.json.gz'
])

es_index_publications = ESIndexPublications(
    task_id=ESIndexPublications.__name__,
    src_s3_key=epmc_metadata_key,
    es_host='elasticsearch',
    max_epmc_metadata=1000,
    dag=dag
)


# structured_references_path = os.path.join(
#     'datalabs-data',
#     'airflow',
#     'output',
#     'policytool-extract',
#     'test-extract-refs-msf.json.gz',
# )
#
# fuzzy_references_path = os.path.join(
#     'datalabs-data',
#     'airflow',
#     'output',
#     'policytool-extract',
#     'test-fuzzy-match-refs-msf.json.gz',
# )
#
# fuzzy_match_refs = FuzzyMatchRefsOperator(
#    task_id='match_refs',
#    es_host='http://elasticsearch:9200',
#    structured_references_path=structured_references_path,
#    fuzzy_matched_references_path=fuzzy_references_path,
#    score_threshold=SCORE_THRESHOLD,
#    should_match_threshold=SHOULD_MATCH_THRESHOLD,
#    dag=dag
# )


pub_path = os.path.join(
    'datalabs-staging',
    'airflow',
    'output',
    'open-research',
    'dimensions',
    'publications',
    'dimensions-publications-2015.json.gz',
)

references_path = os.path.join(
    'datalabs-data',
    'airflow',
    'output',
    'policytool-extract',
    'test-hard-text-match-refs-msf.json.gz',
)

exact_match_refs = ExactMatchRefsOperator(
    task_id='match_refs',
    es_host='http://elasticsearch:9200',
    publications_path=pub_path,
    exact_matched_references_path=references_path,
    title_length_threshold=MIN_TITLE_LENGTH,
    dag=dag
)

exact_match_refs.set_upstream(fetch_epmc_task)
