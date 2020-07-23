# Web API Documentation

Reach web application offers an API for users. It can be accessed at:

`https://reach.wellcomedatalabs.org/api/search/[INDEX]`

Where INDEX is `policy-docs` or `citations`.

## Searching policy documents

To search Policy Documents through the API:

```

GET https://reach.wellcomedatalabs.org/api/search/policy-docs


```

This request must contain at least one `terms` parameter and will search the following fields:
 - Document title
 - Document sub_title
 - Year of publication
 - Source url
 - Publishing organisation

If no order is specified, the request will return the results from the most to the less relevant.

### Parameters


 * `terms`:  (Required) A comma delimited list of terms to search. `terms=foo,bar,baz,foo`
 * `sort`:   The field to sort the response on. `sort=title`
 * `order`:  The order of the sorting. `order=asc` or `order=desc`
 * `page`:   The page to get from the API. Responses are limited to 25 items per-response. `page=1`


### Fields

 The following fields are available for sorting:
 - `title`
 - `source_org`
 - `year`

### Response

A json of the following format:

```
{
  "status": "success",
  "data": [
    {
      "title": "10th FAO/WHO joint meeting on pesticide management: 10-13 April 2017, New Delhi, India",
      "sub_title": null,
      "year": "2017",
      "source_doc_url": "https://apps.who.int/iris/bitstream/handle/10665/255746/WHO-HTM-NTD-WHOPES-2017.03-eng.pdf?sequence=1&isAllowed=y",
      "source_org": "who_iris",
      "scrape_source_page": null,
      "rank": 0.14059973
    },
  ],
  "count": 1,
  "terms": "malaria,africa"
}
```

### Try it:

```

https://reach.wellcomedatalabs.org/api/search/policy-docs?terms=malaria,africa&sort=title&order=asc&page=1

```

## Searching Citations

To search Citations through the API:

```

GET https://reach.wellcomedatalabs.org/api/search/citations


```

This request must contain at least one `terms` parameter and will search the following fields:
 - The associated policy documents':
	 - Document title
	 - Document sub_title
	 - Year of publication
	 - Source url
	 - Publishing organisation

 - The research papers' :
  	 - Title
  	 - Publication journal title
  	 - Year of publication
  	 - Number of associated policies

### Parameters


 * `terms`:  (Required) A comma delimited list of terms to search. `terms=foo,bar,baz,foo`
 * `sort`:   The field to sort the response on. `sort=title`
 * `order`:  The order of the sorting. `order=asc` or `order=desc`
 * `page`:   The page to get from the API. Responses are limited to 25 items per-response. `page=1`


### Fields


The following fields are supported for sorting:

 - `epmc.title`,
 - `epmc.journal_title`,
 - `epmc.pub_year`,
 - `associated_policies_count`,

### Response

A json of the following format:

```

  "status": "success",
  "data": [
    {
      "uuid": "89c77f97-4fcd-4077-b5c0-88d8a8363dc5",
      "id": null,
      "source": null,
      "pmid": "27146406",
      "pmcid": "PMC4857284",
      "doi": "10.1186/s12936-016-1309-3",
      "title": "Assessing the availability of LLINs for continuous distribution through routine antenatal care and the Expanded Programme on Immunizations in sub-Saharan Africa.",
      "authors": [
        {
          "Initials": "K",
          "LastName": "Theiss-Nyland"
        },
        {
          "Initials": "M",
          "LastName": "Lynch"
        },
        {
          "Initials": "J",
          "LastName": "Lines"
        }
      ],
      "journal_title": "Malaria journal",
      "journal_issue": null,
      "journal_volume": "15",
      "pub_year": 2016,
      "journal_issn": "1475-2875",
      "page_info": null,
      "pub_type": "\"Journal Article\"",
      "created": "2020-04-08T16:33:21.257477+00:00",
      "modified": "2020-05-27T13:44:47.962269+00:00",
      "tsv_omni": "'/s12936-016-1309-3':39C '10.1186':38C '27146406':37C 'africa':23A 'and':13A 'antenatal':11A 'assessing':1A 'availability':3A 'care':12A 'continuous':7A 'distribution':8A 'expanded':15A 'for':6A 'immunizations':18A 'in':19A 'journal':35C 'lines':32B,33B 'llins':5A 'lynch':30B,31B 'malaria':34C 'nyland':26B,29B 'of':4A 'on':17A 'pmc4857284':36C 'programme':16A 'routine':10A 'saharan':22A 'sub':21A 'sub-saharan':20A 'the':2A,14A 'theiss':25B,28B 'theiss-nyland':24B,27B 'through':9A",
      "prev_ids": [],
      "source_policies": "{0924e840-13bd-4a6d-9895-78afedfddf08}",
      "rank": 0.030303031,
      "policies": [
        {
          "title": "World malaria report 2016",
          "sub_title": null,
          "year": "2016",
          "source_doc_url": "https://apps.who.int/iris/bitstream/handle/10665/252038/9789241511711-eng.pdf?sequence=1&isAllowed=y",
          "source_org": "who_iris",
          "scrape_source_page": null
        }
      ]
    },
  ],
  "count": 1,
  "terms": "malaria,africa"
}
```

### Try it:

```

https://reach.wellcomedatalabs.org/api/search/citations?terms=malaria,africa&sort=matchtitle.keyword&order=asc&page=1

```
