import json

from web.db import get_db_cur
from .utils import JSONEncoder

SQL = """
SELECT title, sub_title, year, source_doc_url, source_org, scrape_source_page,
        ts_rank_cd(p.tsv_omni, query) AS rank
FROM warehouse.reach_policies AS p,
    websearch_to_tsquery(%s) AS query
WHERE query @@ p.tsv_omni
ORDER BY rank DESC
LIMIT 25
OFFSET %s
"""

SQL_COUNT = """
WITH results AS (
    SELECT uuid,
            ts_rank_cd(p.tsv_omni, query) AS rank
    FROM warehouse.reach_policies AS p,
        websearch_to_tsquery(%s) AS query
    WHERE query @@ p.tsv_omni
) SELECT COUNT(uuid) AS counter FROM results;
"""

class ApiSearchPolicies:

    def __init__(self):
        pass

    def on_get(self, req, resp):

        # TODO: need to rate limit this for external hosts

        if req.params:
            terms = req.params.get("terms", None)
            limit = req.params.get("size", 25)
            page = int(req.params.get("page", 1))

            offset = 0
            if page > 1:
                offset = page * 25

            counter = 0
            results = []
            with get_db_cur() as cur:
                cur.execute(SQL, (
                    terms,
                    offset,
                ))
                results = cur.fetchall()

                cur.execute(SQL_COUNT, (terms,))
                counter = cur.fetchone()
                if counter is not None:
                    counter = counter.get("counter", 0)

            resp.body = json.dumps({
                'status': 'success',
                'data': results,
                'count': counter,
                'terms': terms
            }, cls=JSONEncoder)

        else:
            resp.body = json.dumps({
                'status': 'error',
                'message': 'The request doesn\'t contain any parameters'
            })
