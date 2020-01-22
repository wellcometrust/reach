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


## Further reading
- [Github repository](https://github.com/wellcometrust/reach)
