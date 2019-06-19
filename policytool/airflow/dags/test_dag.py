import datetime
import os
from airflow import DAG
import airflow.utils.dates
from policytool.airflow.tasks.fuzzy_match_refs_operator import FuzzyMatchRefsOperator
from policytool.airflow.tasks.hard_text_match_refs_operator import ExactMatchRefsOperator


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

fuzzy_match_refs = FuzzyMatchRefsOperator(
   task_id='match_refs',
   es_host='http://elasticsearch:9200',
   structured_references_path='datalabs-data/airflow/output/policytool-extract/test-extract-refs-msf.json.gz',
   fuzzy_matched_references_path='datalabs-data/airflow/output/policytool-extract/test-fuzzy-match-refs-msf.json.gz',
   score_threshold=SCORE_THRESHOLD,
   should_match_threshold=SHOULD_MATCH_THRESHOLD,
   dag=dag
)

# exact_match_refs = ExactMatchRefsOperator(
#     task_id='match_refs',
#     es_host='http://elasticsearch:9200',
#     publications_path='datalabs-staging/airflow/output/open-research/dimensions/publications/dimensions-publications-2015.json.gz',
#     hard_text_matched_references_path='datalabs-data/airflow/output/policytool-extract/test-hard-text-match-refs-msf.json.gz',
#     min_title_length=MIN_TITLE_LENGTH,
#     dag=dag
# )
