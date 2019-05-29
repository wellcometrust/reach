import datetime
import os
from airflow import DAG
import airflow.utils.dates

from policytool.airflow.tasks.dummy_spiders_operator import DummySpidersOperator
from policytool.airflow.tasks.extract_refs_operator import ExtractRefsOperator


ORGANISATIONS = [
    'who_iris',
    'nice',
    'gov_uk',
    'msf',
    'unicef',
    'parliament',
]

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

for organisation in ORGANISATIONS:
    run_spider = DummySpidersOperator(
        task_id='run_{spider}_spider'.format(spider=organisation),
        organisation=organisation,
        dag=dag,
    )

parser_model = os.path.join(
        'datalabs-data',
        'reference_parser_models',
        'reference_parser_pipeline.pkl'
        )

organisation = 'msf'
parsed_pdf_file = os.path.join(
        'datalabs-data',
        'airflow',
        'output',
        'policytool-parse',
        'parser-{organisation}'.format(
            organisation=organisation
        ),
        'test-parser-{organisation}.json'.format(
            organisation=organisation)
        )

extracted_refs_path = os.path.join(
        'datalabs-data',
        'airflow',
        'output',
        'policytool-extract',
        'test-extract-refs-{organisation}.json.gz'.format(
            organisation=organisation
        )
        )

extract_refs = ExtractRefsOperator(
    task_id='extract_refs',
    model_path=parser_model,
    src_s3_key=parsed_pdf_file,
    dst_s3_key=extracted_refs_path,
    dag=dag)
