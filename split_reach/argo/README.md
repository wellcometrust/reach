# Argo & Reach
Reach's pipeline is deployed in production using Argo.
These files are for local runs and development.

## How to run Reach's workflows
To run this pipeline locally, you'll need:

  - Docker
  - Minikube
  - Python >= 3.6


To build the required images, go to the `split_reach` folder and run the following:
```
make docker-build
```

To install Argo to your selected cluster (this will install Argo to a namespace `argo`, so make sure it's available before running these commands or change it beforehand):
```
kubectl apply -f argo/00-namespace.yaml
kubectl apply -n argo -f argo/argo.yaml
```

To add test and production workflow to your local Argo:
```
```
