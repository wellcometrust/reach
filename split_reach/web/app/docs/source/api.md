# Web API Documentation

Reach web application offers an API for users. It can be accessed at:

`https://reach-staging.datalabs.wellcome.cloud/api/search/[INDEX]`

Where INDEX is `policy-docs` or `citations`.

## Searching policy documents

To search Policy Documents through the API:

```

GET https://reach.datalabs.wellcome.cloud/api/search/policy-docs


```

This request must contain at least one `terms` and one `fields` parameter.

### Parameters


 * `terms`:  (Required) A comma delimited list of terms to search. `terms=foo,bar,baz,foo`
 * `fields`: (Required) A comma delimited list of fields to search. This must be the same length as terms. First term will be searched in first field, second in second etc. `fields=text,organisation,text,title`
 * `sort`:   The field to sort the response on. `sort=title`
 * `order`:  The order of the sorting. `order=asc` or `order=desc`
 * `page`:   The page to get from the API. Responses are limited to 25 items per-response. `page=1`


### Fields

The following fields are available for search:
 - `title`
 - `text`
 - `organisation`
 - `authors`

 The following fields are available for sorting:
 - `title.keyword`
 - `organisation`
 - `authors.keyword`

### Response

A json of the following format:

```
{
	"took": 7,
	"timed_out": false,
	"_shards":
	{
		"total": 1,
		"successful": 1,
		"skipped": 0,
		"failed": 0
	},
	"hits":
	{
		"total": {"value": 159, "relation": "eq"},
		"max_score": 1.0,
		"hits": [
		{
			"_index": "policy-docs",
			"_type": "_doc",
			"_id": "xxxxxxxxxxxxxxxxxxxx",
			"_score": 1.0,
			"_source":
			{
				"doc":
				{
					"hash": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
					"text": "...",
					"organisation": "foo",
					"title": "foo",
					"authors": foo,
					"created": fpp,
					"year": 2019-01-01,
					"source_page": foo,
					"url": "https://www.foo.example.com"
				}
			}
		}
		]
	},
	"status": "success"
}
```


## Searching Citations

To search Citations through the API:

```

GET https://reach.datalabs.wellcome.cloud/api/search/citations


```

This request must contain at least one `terms` and one `fields` parameter.

### Parameters


 * `terms`:  (Required) A comma delimited list of terms to search. `terms=foo,bar,baz,foo`
 * `fields`: (Required) A comma delimited list of fields to search. This must be the same length as terms. First term will be searched in first field, second in second etc. `fields=text,organisation,text,title`
 * `sort`:   The field to sort the response on. `sort=title`
 * `order`:  The order of the sorting. `order=asc` or `order=desc`
 * `page`:   The page to get from the API. Responses are limited to 25 items per-response. `page=1`


### Fields

The following fields are available for searches:

  - `match_title`
  - `match_algo`
  - `match_pub_year`
  - `match_authors`
  - `match_publication`
  - `match_pmcid`
  - `match_pmid`
  - `match_doi`
  - `match_issn`
  - `match_sources`
  - `policies.doc_id`
  - `policies.source_url`
  - `policies.title`
  - `policies.source_page`
  - `policies.source_page_title`
  - `policies.pdf_creator`
  - `policies.organisation`


The following fields are supported for sorting:

  - `match_title.keyword`
  - `match_pub_year`
  - `match_authors.keyword`
  - `match_publication`
  - `match_pmcid`
  - `match_pmid`
  - `match_doi`
  - `match_issn`
  - `match_sources`
  - `policies.doc_id`
  - `policies.source_url`
  - `policies.title.keyword`
  - `policies.source_page`
  - `policies.source_page_title`
  - `policies.pdf_creator`
  - `policies.organisation`

### Response

A json of the following format:

```
{
	"took":13,
	"timed_out":false,
	"_shards":
	{
		"total":1,
		"successful":1,
		"skipped":0,
		"failed":0
	},
	"hits":
	{
		"total":
		{
			"value":48,
			"relation":"eq"
		},
		"max_score":null,
		"hits": [
			{
				"_index":"policy-citations",
				"_type":"_doc",
				"_id":"xxxxxxxxxxxxxxxxxxxx",
				"_score":null,
				"_source":
				{
					"doc":
					{
						"reference_id":xxxxxxxxxxxxxxxxxxx,
						"extracted_title":"Foo Bar",
						"similarity":42,
						"match_title":"This is such a nice title.",
						"match_algo":"Fuzzy match",
						"match_pub_year":2000,
						"match_authors":"J.Doe",
						"match_publication":"Journal of API publications",
						"match_pmcid":"PMC1111111",
						"match_pmid":11111111,
						"match_doi":"10.1136/jnnp.69.4.464",
						"match_issn":"0022-3050",
						"match_source":"EPMC",
						"policies": [
							{
								"doc_id":"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
								"source_url":"https://www.example.com/pdf-27841361437",
								"title":"Nice title, such a is",
								"source_page": "xxx",
								"source_page_title": "xxx",
								"pdf_creator": "xxx",
								"organisation":"example"
							}
						]
					}
				},
				"sort": ["example"]
			}
		]
	}
}
```
