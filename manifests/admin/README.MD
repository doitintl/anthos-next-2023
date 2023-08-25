# Structure

    .
    └── manifests
        ├── admin: root directory of all admin manifests
        │   ├── README.MD
        │   ├── namespaces.yaml
        │   ├── rbac
        │   │   ├── user auth manifests
        │   └── repo-syncs: each file is a repo sync for given namespace
        │       └── capture.yaml
        └── apps: application manifests 
            ├── README.md
            └── capture
                └── deployment.yaml

# Creating a new namepspace

Make sure once a new namespace is creatd, and a reposync is configured for it, you add a git secret in the namespace so it can pull

from doit-1:

    kubectl create secret generic git-creds  --namespace=YOUR-NAMESPACE  --from-file=ssh=/home/doit/.ssh/id_rsa_github 