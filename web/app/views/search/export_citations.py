import json
import csv
import os
import tempfile
import datetime
from io import BytesIO


import falcon

from web.db import get_db_cur


CSV_EXPORT = """
COPY (
WITH results AS (
        SELECT epmc.*, cites.policies
        FROM warehouse.epmc_metadata AS epmc
        LEFT JOIN warehouse.reach_citations AS cites ON cites.epmc_id = epmc.uuid
        WHERE websearch_to_tsquery('Hypertension and chinese medicine') @@ epmc.tsv_omni
    ) SELECT r.*,
             ts_rank_cd(r.tsv_omni, websearch_to_tsquery('Hypertension and chinese medicine')) AS rank,
             p.title AS policy_title,
             p.sub_title AS policy_sub_title,
             p.year AS policy_year,
             p.source_doc_url AS policy_doc_url,
             p.source_org AS policy_org,
             p.scrape_source_page AS policy_source_page
        FROM results AS r
        LEFT JOIN warehouse.reach_policies AS p ON p.uuid = ANY(r.policies)
    )
TO STDOUT
WITH CSV HEADER;
"""

JSON_EXPORT = """
COPY (SELECT json_agg(t) FROM (
    WITH results AS (
        SELECT *,
                ts_rank_cd(epmc.tsv_omni, query) AS rank
        FROM warehouse.epmc_metadata AS epmc,
            websearch_to_tsquery('{TERMS}') AS query
        WHERE query @@ epmc.tsv_omni
        ORDER BY rank DESC
    ) SELECT r.*,
        (SELECT json_agg(items)
            FROM (
                        SELECT title, sub_title, year, source_doc_url, source_org, scrape_source_page FROM warehouse.reach_policies AS cp
                WHERE c.policies @> ARRAY[cp.uuid]::UUID[]

                ) AS items
            ) AS policies
    FROM results AS r
    LEFT JOIN warehouse.reach_citations as c ON c.epmc_id = r.uuid
) t) TO STDOUT WITH NULL AS 'null';
"""

def clean_up_file(req, resp, resource):
    # Quick way to delete a file and handle it if it doesn't
    # exist
    try:
        os.remove(resource.temp_file)
    except OSError:
        pass


class ExportCitationsSearch:
    def __init__(self):
        self.file_name = "reach-citations-export-{isodate}".format(
            isodate=datetime.datetime.now().isoformat()
        )
        self.temp_file = None

    @falcon.after(clean_up_file)
    def on_get(self, req, resp, ftype):
        if not req.params:
            resp.body = json.dumps({
                "status": "error",
                "message": "The request doesn't contain any parameters"
            })
            resp.status = falcon.HTTP_400

        params = req.params
        term = params.get("terms", None)

        if term is None:
            return None

        try:
            if ftype == 'csv':
                resp.content_type = "text/csv"
                resp.append_header(
                    'Content-Disposition',
                    'attachment; filename="{filename}.csv"'.format(
                        filename=self.file_name
                    )
                )

                # We do this because BytesIO is too slow with large
                # queries
                self.temp_file = None
                with tempfile.NamedTemporaryFile(delete=False) as f:
                    self.temp_file = f.name
                    with get_db_cur() as cur:
                        cur.copy_expert(CSV_EXPORT.replace("{TERMS}", term), f)

                # Falcon calls close on the object
                resp.stream = open(self.temp_file, "r")


            else:
                resp.content_type = "text/json"
                resp.append_header(
                    'Content-Disposition',
                    'attachment; filename="{filename}.json"'.format(
                        filename=self.file_name,
                    )
                )

                self.temp_file = None
                with tempfile.NamedTemporaryFile(delete=False) as f:
                    self.temp_file = f.name
                    with get_db_cur() as cur:
                        cur.copy_expert(JSON_EXPORT.replace("{TERMS}", term), f)

                # Falcon calls close on the object
                resp.stream = open(self.temp_file, "r")

        except Exception as e:
            raise(e)
            resp.body = json.dumps({
                'status': 'error',
                'message': e
            })






