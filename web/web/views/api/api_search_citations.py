import json

from psycopg2.extensions import AsIs

from web.db import get_db_cur
from .utils import JSONEncoder

# The reason we use a WITH here is so that the json agg
# function we use in outer doesn't end up getting called for all
# items in the table, it only gets called for the results of our
# specific query
SQL = """
WITH results AS (
    SELECT epmc.*,
           rc.policies AS source_policies,
           rc.uuid,
           ts_rank_cd(epmc.tsv_omni, query) as rank
    FROM warehouse.epmc_metadata AS epmc
    LEFT JOIN warehouse.reach_citations AS rc ON rc.epmc_id = epmc.uuid
    CROSS JOIN websearch_to_tsquery(%s) AS query
    WHERE array_length(rc.policies, 1) > 0
        AND query @@ epmc.tsv_omni
    ORDER BY %s %s
    LIMIT %s
    OFFSET %s
) SELECT r.*,
         (SELECT json_agg(items)
             FROM (
                  SELECT title, sub_title, year, source_doc_url, source_org,
                         scrape_source_page FROM warehouse.reach_policies AS cp
                 WHERE r.source_policies @> ARRAY[cp.uuid]::UUID[]
                      ) AS items
             ) AS policies
FROM results AS r;
"""

SQL_COUNT = """
WITH results AS (
    SELECT epmc.uuid,
            ts_rank_cd(epmc.tsv_omni, query) AS rank
    FROM warehouse.epmc_metadata AS epmc
        LEFT JOIN warehouse.reach_citations AS rc ON rc.epmc_id = epmc.uuid
        CROSS JOIN websearch_to_tsquery(%s) AS query
    WHERE query @@ epmc.tsv_omni
        AND array_length(rc.policies, 1) > 0
) SELECT COUNT(uuid) AS counter FROM results;
"""

DEFAULT_ORDER = ("rank", "DESC",)
ALLOWABLE_ORDERS = (
    "epmc.title",
    "epmc.journal_title",
    "epmc.pub_year",
    "associated_policies_count",
)


class ApiSearchCitations:

    def __init__(self):
        pass

    def on_get(self, req, resp):
        """Returns the result of a search on the postgres citations data.

        Args:
            req: The request passed to this controller
            resp: The reponse object to be returned
        """

        # TODO: Need to rate-limit this for external hosts

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

            offset = 0
            if page > 1:
                offset = (page - 1) * int(limit)

            counter = 0
            results = []

            # TODO: These terms need to be changed on the frontend
            if sort is None:
                orders = DEFAULT_ORDER
            else:
                if sort == "associated_policies_count":
                    orders = ("array_length(rc.policies, 1)", order)
                else:
                    orders = (sort, order)

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
