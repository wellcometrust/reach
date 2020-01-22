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

The following fields are available on the search API:
 - title
 - text
 - organisation
 - authors

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
