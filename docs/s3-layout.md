# policytool Airflow task S3 layout

This document describes how policytool tasks write to S3.

## S3 layout

In general, we're pursuing a layout of the format:

```
s3://${BUCKET_NAME}/airflow/output/${DAG_NAME}/${TASK_NAME}/
        ${DAG_NAME}--${TASK_NAME}.json.gz
```

So to explain this in practice, we need to talk about:

1. The DAGs we plan to deploy, and
1. The tasks inside each of those dags


## A list of DAGs

At any time, there will be multiple DAGs running for the policy tool,
including:

1. `policytool-scrape`: scrapes all policy organizations.
1. `policytool-epmc-pubs`: fetches publications from EPMC.
1. `policytool-match-dimensions-pubs`: matches publications from dimensions
1. `policytool-match-epmc-pubs`: matches publications from EPMC
1. `policytool-test`: combines the DAGs above, but only uses a small number of policy documents.


## `policytool.scrape`

There's one task per organization in `policytool.scrape`. Task names would include:

- `scraper-who`
- `scraper-msf`
- `scraper-govuk`

A final task may also be added to summarize their results into a single output:

- `summary`

So, some example S3 outputs for this DAG are:

```
s3://${BUCKET_NAME}/airflow/output/policytool-scrape/scraper-who/policytool-scrape--scraper-who.json.gz
s3://${BUCKET_NAME}/airflow/output/policytool-scrape/scraper-who/pdf/0a/0a4cb4bebf2a177e43dc36274820880cdcacb2.pdf
s3://${BUCKET_NAME}/airflow/output/policytool-scrape/summary/policytool-scrape--summary.json.gz
```

## `policytool-epmc-pubs`

One task per year will be present in `policytool.epmc-pubs`, with task names of format:

- `pubs-2000`
- `pubs-2001`
- ...
- `pubs-2019`

A final task will be present to concatenate all publications:

- `epmc-pubs-concat`

So, some example S3 outputs for this DAG are:

```
s3://${BUCKET_NAME}/airflow/output/policytool-epmc-pubs/pubs-2000/policytool-epmc-pubs--pubs-2000.json.gz
...
s3://${BUCKET_NAME}/airflow/output/policytool-epmc-pubs/pubs-concat/policytool-epmc-pubs--pubs-concat.json.gz
```



## `policytool-match-*`

One `policytool.match` DAG exists for each publication source. Each such DAG should produce citations for 1 to N policy organizations.

Looking at the part of the DAG that is specific to a single policy
organization, we see:

```
scraper-${ORGANIZATION} --------------------> refparser-${ORGANIZATION}
(from policytool.scrape)                       |
                                               |
                                               v
publications -------------------------------> matcher-${ORGANIZATION} 
(from policytool.epmc-pubs or outside DAG)     |
                                               |
                                               v
                                              concat-matches
```

Key steps:

1. A scraper, in the `policytool-scrape` DAg, pulls PDF from an organization's
   websites, storing each of them to S3 and writing a `manifest.json` file
   containing the list of all scraped PDFs and other metadata.
1. A refparser extracts references from all PDFs listed by a 
   `manifest.json` and writes them to an output `references.json` 
   file.
1. A matcher reads from all publications, and from a `references.json`,
   producing matched referencies (citations) and writing them to an
   output `citations.json` file.

Task names in this DAG include:


- `refparser-who`
- `refparser-msf`
- ...
- `matcher-who`
- `matcher-msf`
- ...
- `concat-matches`


So, some example S3 outputs for this DAG are:

```
s3://${BUCKET_NAME}/airflow/output/policytool-match-epmc-pubs/refparser-who/
    policytool-match-epmc-pubs--refparser-who.json.gz
s3://${BUCKET_NAME}/airflow/output/policytool-match-epmc-pubs/matcher-msf/
    policytool-match-epmc-pubs--matcher-msf.json.gz
s3://${BUCKET_NAME}/airflow/output/policytool-match-epmc-pubs/concat-matches/
    policytool-match-epmc-pubs--concat-matches.json.gz
```

