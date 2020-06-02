import json

from web.db import get_db_cur
from .utils import JSONEncoder

# The reason we use a WITH here is so that the json agg
# function we use in outer doesn't end up getting called for all
# items in the table, it only gets called for the results of our
# specific query
SQL = """
WITH results AS (
    SELECT *,
            ts_rank_cd(epmc.tsv_omni, query) AS rank
    FROM warehouse.epmc_metadata AS epmc,
        websearch_to_tsquery(%s) AS query
    WHERE query @@ epmc.tsv_omni
    ORDER BY rank DESC
    LIMIT 25
    OFFSET %s
) SELECT r.*,
    (SELECT json_agg(items)
        FROM (
                    SELECT title, sub_title, year, source_doc_url, source_org, scrape_source_page FROM warehouse.reach_policies AS cp
            WHERE c.policies @> ARRAY[cp.uuid]::UUID[]

            ) AS items
        ) AS policies
FROM results AS r
LEFT JOIN warehouse.reach_citations as c ON c.epmc_id = r.uuid;
"""

SQL_COUNT = """
WITH results AS (
    SELECT uuid,
            ts_rank_cd(epmc.tsv_omni, query) AS rank
    FROM warehouse.epmc_metadata AS epmc,
        websearch_to_tsquery(%s) AS query
    WHERE query @@ epmc.tsv_omni
) SELECT COUNT(uuid) AS counter FROM results;
"""

class ApiSearchCitations:

    def __init__(self):
        pass

    def on_get(self, req, resp):
        """Returns the result of a search on the postgres citations data.

        Args:
            req: The request passed to this controller
            resp: The reponse object to be returned
        """

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
                'count': counter
            }, cls=JSONEncoder)


        else:
            resp.body = json.dumps({
                'status': 'error',
                'message': 'The request doesn\'t contain any parameters'
            })


