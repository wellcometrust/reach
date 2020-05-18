# Argo & Reach
Reach's pipeline is deployed in production using Argo.
These files are for local runs and development.

## How to run Reach's workflows
To run this pipeline locally, you'll need:

  - Docker
  - Minikube
  - Python >= 3.6
  - The Argo cli (recommended but optionnal)


To build the required images, go to the root folder and run the following:
```
make docker-build
```

To install Argo to your selected cluster (this will install Argo to a namespace `argo`, so make sure it's available before running these commands or change it beforehand):
```
kubectl apply -f argo/00-namespace.yaml
kubectl apply -f argo/argo.yaml
kubectl apply -f argo/elasticsearch.yaml
kubectl apply -f argo/psqlinit.yaml
kubectl apply -f argo/postgres.yamls
```


You can then run your workflows as follows:
```
# this is the example workflow for WHO IRIS
argo submit -n argo argo/reach-who.yaml
```

## Using this infrastructure with the web application
Reach's web application only relies on Postgresql. To expose it and make it usable locally (or within the `docker-compose` local deployment), run:
```
kubectl port-forward -n argo postgres-0 5432:5432
```
