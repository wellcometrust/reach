"""
DAG to run the policy tool on every organisation.
"""

import datetime
import os
from airflow import DAG
import airflow.utils.dates

from policytool.airflow.tasks.run_spiders_operator import RunSpiderOperator
from policytool.airflow.tasks.parse_pdf_operator import ParsePdfOperator
from policytool.airflow.tasks.extract_refs_operator import ExtractRefsOperator

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

    parsed_pdf_file = os.path.join(
        parsing_path,
        'policytool-parse--parser-{organisation}.json'.format(
            organisation=organisation
        )
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

    extract_refs.set_upstream(pdfParsing)

