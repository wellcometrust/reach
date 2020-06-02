import json
import csv
import tempfile
import os
import datetime
from io import BytesIO


import falcon

from web.db import get_db_cur


CSV_EXPORT = """
COPY (SELECT title, sub_title, year, source_doc_url, source_org, scrape_source_page,
            ts_rank_cd(p.tsv_omni, query) AS rank
    FROM warehouse.reach_policies AS p,
        websearch_to_tsquery('{TERMS}') AS query
    WHERE query @@ p.tsv_omni
    ORDER BY rank DESC)
TO STDOUT
WITH CSV HEADER;
"""

JSON_EXPORT = """
COPY (SELECT json_agg(t) FROM (
    SELECT title, sub_title, year, source_doc_url, source_org, scrape_source_page,
            ts_rank_cd(p.tsv_omni, query) AS rank
    FROM warehouse.reach_policies AS p,
        websearch_to_tsquery('{TERMS}') AS query
    WHERE query @@ p.tsv_omni
    ORDER BY rank DESC
) t)
TO STDOUT WITH NULL AS 'null'
"""

def clean_up_file(req, resp, resource):
    # Quick way to delete a file and handle it if it doesn't
    # exist
    try:
        os.remove(resource.temp_file)
    except OSError:
        pass

class ExportPoliciesSearch:
    def __init__(self):
        self.file_name = "reach-policies-export-{isodate}".format(
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






