import json

from reach.web.views import search


VALID_BODY = json.dumps({
    "size": 25,
    "query": {
        "bool": {
            "should": [
                {"terms": {"doc.text": ["bar", "baz"]}},
                {"terms": {"doc.title": ["foo"]}},
                {"terms": {"doc.organisation": ["nice"]}},
                {"terms": {"doc.authors": ["J.Doe"]}}
            ],
            "minimum_should_match": 1
        }
    },
    "sort": {"doc.organisation": "asc"}
})


def test_query_builder():
    """Tests that the query builder builds queries the right way."""

    params = {
        "terms": ','.join([
            "bar",
            "foo",
            "baz",
            "nice",
            "J.Doe",
        ]),
        "fields": ','.join([
            "text",
            "title",
            "text",
            "organisation",
            "authors",
        ]),
        "sort": "organisation"
    }

    search_body = search._build_es_query(params)

    assert json.dumps(search_body) == VALID_BODY
