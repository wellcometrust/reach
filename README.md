# Wellcome Reach

Wellcome Reach is an open source service for discovering how research
publications are cited in global policy documents, including those
produced by policy organizations such as the WHO, MSF, and the UK
government. Key parts of it include:

1. Web scrapers for pulling PDF "policy documents" from policy
   organizations,
1. A reference parser for extracting references from these documents,
1. A task for sourcing publications from Europe PMC (EPMC),
1. A task for matching policy document references to EPMC publications,
1. An Airflow installation for automating the above tasks, and
1. A web application for searching and retrieving data from the datasets
   produced above.

Wellcome Reach is written in Python and developed using docker-compose.
It's deployed into Kubernetes.

Although parts of the Wellcome Reach have been in use at Wellcome since
mid-2018, the project has only been open source since March 2019. Given
these early days, please be patient as various parts of it are made
accessible to external users. All issues and pull requests are welcome.
Contributing guidelines can be found in
[CONTRIBUTING.md](./CONTRIBUTING.md).

## Development

### Dependencies

To develop for this project, you will need:

1. Python 3.6+, plus `pip` and `virtualenv`
1. Docker and docker-compose
1. AWS credentials with read/write S3 permissions to an S3 bucket
   of your choosing.

### docker-compose

To bring up the development environment using docker:

1. Set your AWS credentials into your environment. (`AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`)
1. Build and start the env with:
    ```
    make docker-build
    docker-compose up -d
    ```
1. Verify it all came up with:
    ```
    docker-compose ps
    ```

Once up, you'll be able to access:

- airflow on http://localhost:8080/
- Elasticsearch on http://localhost:9200/
- the website on http://localhost:8081/


### virtualenv

For local development outside of airflow or other services, use the
project's virtualenv:

```
make virtualenv
source build/virtualenv/bin/activate
```


### Testing

To run all tests for the project using the official Python version and
other dependencies, run:

```
make docker-test
```

You can also run tests locally using the project's virtualenv, with

```
make test
```

or using the appropriate pytest command, as documented in `Makefile`.


### Airflow

Wellcome Reach uses Apache Airflow to automate running its data
pipelines. Specifically, we've broken down the batch pipeline into a
series of dependent steps, all part of a Directed Acyclic Graph (DAG).


#### Running a task in airflow

It's quite common to want to run a single task in Airflow without having
to click through in the UI, not least because all logging messages are
then on the console. To do this, from top of the project directory:

1. Bring up the stack with `docker-compose` as shown above, and
1. Run the following command, substituting for `DAG_NAME`, `TASK_NAME`, and
   `JSON_PARAMS`:
    ```
    ./docker_exec.sh airflow test \
        ${DAG_NAME} ${TASK_NAME} \
	    2018-11-02 -tp '${JSON_PARAMS}'
    ```

### For developers inside Wellcome

Although not required, you can add Sentry reporting from your local dev
environment to a localdev project inside Wellcome's sentry account by
running:

    ```
    eval $(./export_wellcome_env.py)
    ```

before running `docker-compose up -d` above.


## Deployment

For production, a typical deployment uses:

- a Kubernetes cluster that supports persistent volumes
- a PostgreSQL or MySQL database for Airflow to use
- a distributed storage service such as S3
- an ElasticSearch cluster for searching documents

## Evaluation

The evaluation results are stored as an output [here](https://s3.console.aws.amazon.com/s3/buckets/datalabs-staging?region=eu-west-1&prefix=reach/evaluation/evaluations/). Broadly the evaluation works by comparing a gold set of results - a manually annotated dataset of all the publications that should be found in a sample of policy documents, against the publications Reach identified in the same sample of policy documents. The evaluation script is held in another private repo.

## Further reading

- [Deep reference parser](https://github.com/wellcometrust/deep_reference_parser)
- [Argo](reach⁩/argo⁩/README.md)
- [Scraping](reach⁩/pipeline⁩/reach-scraper⁩/README.md)

## Contributing

See the [Contributing guidelines](./CONTRIBUTING.md)
