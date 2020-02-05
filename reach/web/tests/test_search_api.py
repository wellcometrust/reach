import json

from reach.web.views import search


def test_query_builder():
    """Tests that the query builder builds queries the right way."""

    valid_body = json.dumps({
        "size": 25,
        "query": {
            "bool": {
                "should": [
                    {"terms_set": {
                        "doc.text": {
                            "terms":  ["bar", "baz"],
                            "minimum_should_match_script": {
                                "source": "2"
                            }
                        }
                    }},
                    {"terms_set": {
                        "doc.title": {
                            "terms":  ["foo"],
                            "minimum_should_match_script": {
                                "source": "1"
                            }
                        }
                    }},
                    {"terms_set": {
                        "doc.organisation": {
                            "terms":  ["nice"],
                            "minimum_should_match_script": {
                                "source": "1"
                            }
                        }
                    }},
                    {"terms_set": {
                        "doc.authors": {
                            "terms":  ["J.Doe"],
                            "minimum_should_match_script": {
                                "source": "1"
                            }
                        }
                    }},
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
                    {"terms_set": {
                        "doc.text": {
                            "terms":  ["bar", "baz", "foo", "kix"],
                            "minimum_should_match_script": {
                                "source": "4"
                            }
                        }
                    }},
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
                    {"terms_set": {
                        "doc.text": {
                            "terms":  ["bar", "baz", "foo", "kix"],
                            "minimum_should_match_script": {
                                "source": "4"
                            }
                        }
                    }},

                    {"terms_set": {
                        "doc.title": {
                            "terms":  [
                                "pizza",
                                "celery",
                                "brocoli",
                                "mayo",
                            ],
                            "minimum_should_match_script": {
                                "source": "4"
                            }
                        }
                    }},
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
