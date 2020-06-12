import json

from psycopg2.extensions import AsIs

from web.db import get_db_cur
from .utils import JSONEncoder


SQL = """
SELECT title, sub_title, year, source_doc_url, source_org, scrape_source_page,
        ts_rank_cd(p.tsv_omni, query) AS rank
FROM warehouse.reach_policies AS p,
    websearch_to_tsquery(%s) AS query
WHERE query @@ p.tsv_omni
ORDER BY %s %s
LIMIT %s
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

DEFAULT_ORDER = ("rank", "DESC")
ALLOWABLE_ORDERS = (
    "title",
    "source_org",
    "year"
)


class ApiSearchPolicies:

    def __init__(self):
        pass

    def on_get(self, req, resp):

        # TODO: need to rate limit this for external hosts

        if req.params:
            sort = req.params.get("sort", None)
            order = req.params.get("order", "DESC")
            terms = req.params.get("terms", None)
            limit = req.params.get("size", 25)
            page = int(req.params.get("page", 1))

            if order.upper() not in (None, "DESC", "ASC",):
                resp.content_type = "application/json"
                resp.body = json.dumps({
                    'status': 'error',
                    'message': "Invalid ordering operation"
                })
                return

            if sort not in ALLOWABLE_ORDERS:
                resp.content_type = "application/json"
                resp.body = json.dumps({
                    'status': 'error',
                    'message': "Invalid ordering operation"
                })
                return

            if sort is None:
                orders = DEFAULT_ORDER
            else:
                orders = (sort, order)

            offset = 0
            if page > 1:
                offset = (page - 1) * int(limit)

            counter = 0
            results = []
            with get_db_cur() as cur:
                cur.execute(SQL, (
                    terms,
                    AsIs(orders[0]),
                    AsIs(orders[1]),
                    limit,
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
