import datetime

from airflow import DAG
import airflow.utils.dates

from policytool.airflow.tasks.dummy_spiders_operator import DummySpidersOperator


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
