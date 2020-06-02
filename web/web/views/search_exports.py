import json
import csv
import tempfile
import datetime

import falcon

from web.views import search


CSV_COPY_QUERY = """
COPY {sql_query}
TO STDOUT
WITH CSV HEADER;
"""

JSON_COPY_QUERY = """
COPY
    WITH t AS (
        {sql_query}
        )
    SELECT json_agg(t) FROM t
TO STDOUT
WITH TEXT;
"""


class ResultsExport:
    """Let you search for terms in publications fulltexts. Returns a json.

    Args:
        es: An elasticsearch connection
        es_index: The index to search on
        es_explain: A boolean to enable|disable elasticsearch's explain.

    """

    def __init__(self, db, source):
        self.db = db
        self.source = source

    def on_get(self, req, resp, ftype):
        """Returns the result of a search on the elasticsearch cluster.

        Args:
            req: The request passed to this controller
            resp: The reponse object to be returned
        """

        if not req.params:
            resp.body = json.dumps({
                'status': 'error',
                'message': "The request doesn't contain any parameters"
            })
            resp.status = falcon.HTTP_400

        # Get total number of results
        params = req.params
        params['size'] = 1
        params['fields'] = self.search_fields

        # Expects parameters and table. parameters are in [terms, fields, size,
        # page, sort and order].
        # Needs at least terms and fields
        built_query = search._build_psql_query(
            params,
            self.source,
        )

        try:
            cur = self.db._get_cur()
            if ftype == 'csv':
                resp.content_type = 'text/csv'
                resp.append_header(
                    'Content-Disposition',
                    'attachment; filename="{filename}.csv"'.format(
                        filename=self.file_name
                    )
                )
                # Falcon will call resp.stream.close()
                sql_query = CSV_COPY_QUERY.format(
                    sql_query=built_query
                )
                cur.copy_expert(sql_query, resp.stream)
            else:
                # Assumes everything else is json. Safer & memory effective

                resp.content_type = 'text/json'
                resp.append_header(
                    'Content-Disposition',
                    'attachment; filename="{filename}.json"'.format(
                        filename=self.file_name
                    )
                )

                sql_query = JSON_COPY_QUERY.format(
                    sql_query=built_query,
                )

                cur.copy_expert(sql_query, resp.stream)

        except Exception as e:  # noqa
            raise(e)
            resp.body = json.dumps({
                'status': 'error',
                'message': e
            })


# class CitationsExport(ResultsExport):
#
#     def __init__(self, db):
#         self.search_fields = ','.join([
#             'match_title',
#             'policies.title',
#             'policies.organisation',
#             'match_source',
#             'match_publication',
#             'match_authors'
#         ])
#
#         self.file_name = "reach-citations-export-{isodate}".format(
#             isodate=datetime.datetime.now().isoformat()
#         )
#
#         super(CitationsExport, self).__init__(db)
#
#     def get_headers(self, response):
#         doc = response['hits']['hits'][0]['_source']['doc']
#         policy_headers = []
#
#         if not len(doc['policies']):
#             return doc.keys()[:-1], []
#
#         for key in doc['policies'][0].keys():
#             policy_headers.append('policies.{key_name}'.format(key_name=key))
#
#         return list(doc.keys())[:-1], policy_headers
#
#     def yield_rows(self, headers, policy_headers, data):
#         for item in data['hits']['hits']:
#             for policy in item['_source']['doc']['policies']:
#                 row = {}
#                 for key in headers:
#                     row[key] = item['_source']['doc'][key]
#                 for key in policy_headers:
#                     row[key] = policy[key.replace(
#                         'policies.', ''
#                     )]
#
#                 yield row
#
#
# class PolicyDocsExport(ResultsExport):
#
#     def __init__(self, db):
#         self.search_fields = ','.join([
#             'title',
#             'text',
#             'organisation',
#             'authors',
#         ])
#
#         self.file_name = "reach-policy-docs-export-{isodate}".format(
#             isodate=datetime.datetime.now().isoformat()
#         )
#
#         super(PolicyDocsExport, self).__init__(db)
#
#     def get_headers(self, response):
#         return list(response['hits']['hits'][0]['_source']['doc'].keys()), []
#
#     def yield_rows(self, headers, policy_headers, data):
#         for item in data['hits']['hits']:
#             yield item['_source']['doc']
