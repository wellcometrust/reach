"""
DAG to run the policy tool on every organisation.
"""

import datetime
import os
from airflow import DAG
import airflow.utils.dates

from scraper.airflow.tasks.run_spiders_operator import RunSpiderOperator
from scraper.airflow.tasks.parse_pdf_operator import ParsePdfOperator

ORGANISATIONS = [
    'who_iris',
    'nice',
    'gov_uk',
    'unicef',
    'parliament',
    'msf',
]

args = {
    'depends_on_past': False,
    'start_date': airflow.utils.dates.days_ago(2),
    'retries': 0,
    'retry_delay': datetime.timedelta(minutes=5),
}

dag = DAG(
    dag_id='policytool_dag',
    default_args=args,
    schedule_interval='0 0 * * 0'
)

for organisation in ORGANISATIONS:
    scraping_path = os.path.join(
        'datalabs-data',
        'airflow',
        'output',
        'policytool-scrape',
        'scraper-{organisation}'.format(
            organisation=organisation
        ),
    )
    run_spider = RunSpiderOperator(
        task_id='run_{spider}_spider'.format(spider=organisation),
        organisation=organisation,
        path=scraping_path,
        dag=dag,
    )

    parsing_path = os.path.join(
        'datalabs-data',
        'airflow',
        'output',
        'policytool-parse',
        'parser-{organisation}'.format(
            organisation=organisation
        ),
    )
    pdfParsing = ParsePdfOperator(
        task_id='run_{organisation}_parser'.format(organisation=organisation),
        organisation=organisation,
        input_path=scraping_path,
        output_path=parsing_path,
        dag=dag,
    )
    pdfParsing.set_upstream(run_spider)
