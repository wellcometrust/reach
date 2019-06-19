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
from policytool.airflow.tasks.fuzzy_match_refs_operator import FuzzyMatchRefsOperator
from policytool.airflow.tasks.hard_text_match_refs_operator import ExactMatchRefsOperator


ORGANISATIONS = [
    'who_iris',
    'nice',
    'gov_uk',
    'unicef',
    'parliament',
    'msf',
]

MIN_TITLE_LEGTH = 40

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
    output_path = os.path.join(
        'datalabs-data',
        'airflow',
        'output'
    )
    scraping_path = os.path.join(
        output_path,
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
        output_path,
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
        output_path,
        'policytool-extract',
        'test-extract-refs-{organisation}.json.gz'.format(
            organisation=organisation
        )
    )
    extractRefs = ExtractRefsOperator(
        task_id='extract_refs',
        model_path=parser_model,
        src_s3_key=parsed_pdf_file,
        dst_s3_key=extracted_refs_path,
        dag=dag
    )
    extract_refs.set_upstream(pdfParsing)

    fm_references_path = os.path.join(
        output_path
        'policytool-extract',
        'fuzzy-match-refs-{organisation}.json.gz'.format(organisation=organisation)
    )
    fmMatching = FuzztMatchRefsOperator(
        task_id='fuzzy_match_refs',
        es_host='http://elasticsearch:9200',
        structured_references_path=output_path,
        fuzzy_matched_references_path=fm_references_path,
        dag=dag
    )
    fmMatching.set_upstream(extractRefs)
    for year in range(2000,2019):
        em_references_path = os.path.join(
            output_path
            'policytool-extract',
            'exact-match-refs-{organisation}-{year}.json.gz'.format(
                organisation=organisation,
                year=year
            )
        )
        publications_path = os.path.join(
            output_path,
            'open-research',
            'dimensions',
            'publications'
            'dimensions-publications-{year}.json.gz'.format(year=year)
        )
        emMatching = ExactMatchRefsOperator(
            task_id='hard_match_refs',
            es_host='http://elasticsearch:9200',
            publications_path=publications_path,
            hard_text_matched_references_path=em_references_path,
            min_title_length=MIN_TITLE_LENGTH,
            dag=dag
        )
        emMatching.set_upstream(pdfParsing)
