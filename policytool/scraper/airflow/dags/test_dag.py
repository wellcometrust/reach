import datetime

from airflow import DAG
import airflow.utils.dates


from scraper.airflow.tasks.hello_world_task import TestTaskOperator
from scraper.airflow.tasks.run_spider import RunSpiderOperator


ORGANISATIONS = [
    'who_iris',
    # 'nice',
    # 'gov',
    # 'msf',
    # 'unicef',
    # 'parliament',
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

# hello_world_task = TestTaskOperator(
#     task_id='print_hello_world',
#     dag=dag,
# )


for organisation in ORGANISATIONS:
    run_spider = RunSpiderOperator(
        task_id='run_{spider}_spider'.format(spider=organisation),
        organisation=organisation,
        dag=dag,
    )
