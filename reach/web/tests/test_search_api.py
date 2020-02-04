import json

from reach.web.views import search


def test_query_builder():
    """Tests that the query builder builds queries the right way."""

    valid_body = json.dumps({
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

    assert json.dumps(search_body) == valid_body


def test_sentence_query_builder():
    """Tests that the query builder builds queries the right way."""

    valid_body = json.dumps({
        "size": 25,
        "query": {
            "bool": {
                "should": [
                    {"terms": {"doc.text": ["bar", "baz", "foo", "kix"]}},
                ],
                "minimum_should_match": 1
            }
        },
        "sort": {"doc.organisation": "asc"}
    })

    params = {
        "terms": ','.join([
            "bar baz foo kix",
        ]),
        "fields": ','.join([
            "text",
        ]),
        "sort": "organisation"
    }

    assert json.dumps(search._build_es_query(params)) == valid_body


def test_multi_sentences_query_builder():
    """Tests that the query builder builds queries the right way."""

    valid_body = json.dumps({
        "size": 25,
        "query": {
            "bool": {
                "should": [
                    {"terms": {"doc.text": ["bar", "baz", "foo", "kix"]}},
                    {"terms": {"doc.title": [
                        "pizza",
                        "celery",
                        "brocoli",
                        "mayo",
                    ]}},
                ],
                "minimum_should_match": 1
            }
        },
        "sort": {"doc.organisation": "asc"}
    })

    params = {
        "terms": ','.join([
            "bar baz foo kix",
            "pizza celery brocoli mayo",
        ]),
        "fields": ','.join([
            "text",
            "title"
        ]),
        "sort": "organisation"
    }

    assert json.dumps(search._build_es_query(params)) == valid_body

    params = {
        "terms": ','.join([
            "bar baz",
            "pizza celery brocoli mayo",
            "foo kix",
        ]),
        "fields": ','.join([
            "text",
            "title",
            "text"
        ]),
        "sort": "organisation"
    }
    assert json.dumps(search._build_es_query(params)) == valid_body
