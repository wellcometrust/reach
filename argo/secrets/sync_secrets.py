#!/usr/bin/env python3

"""
Pushes secrets from this repo to the currect K8S cluster.

This tool assumes the following directory structure for the
directory passed to it:

  /path/to/${CLUSTER_NAME}/
      ${NAMESPACE}/
          ${SECRET_NAME}/
              ${KEY_NAME}

Where one ${KEY_NAME} file exists for every secret attribute. (Key here
refers to key/value, not a KMS key). See README.md for how these files
are created and more details.
"""


from argparse import ArgumentParser
import os.path
import sys
import base64

import kubernetes


parser = ArgumentParser(description=__doc__.strip())
parser.add_argument(
    'cluster_secrets_dir',
    help='Path to directory of cluster secrets, e.g. k8s/datalabs-prod0'
)
parser.add_argument(
    '-n', dest='do_nothing', action='store_true',
    help='Do nothing; just print what we would do.'
)


def check_cluster_name(cluster_name):
    """ Verifes that $KUBECONFIG points to cluster of name cluster_name.
    Exits 1 if not.
    """
    _, context = kubernetes.config.list_kube_config_contexts()
    actual_name = os.path.basename(context['name'])
    if not cluster_name == actual_name:
        sys.stderr.write(
            "Error: %s doesn't match cluster names in $KUBECONFIG (%s)\n" %
            (cluster_name, actual_name)
        )
        sys.exit(1)


def read_ciphertext(path):
    """ Reads ciphertext from a path and returns its plaintext. """
    with open(path, 'rb') as f:
        ciphertext = base64.b64decode(f.read())
    return ciphertext


def encode_payload(plaintext):
    """ Encodes a plaintext payload for use in a K8S secret. """
    return base64.b64encode(
        plaintext
    ).decode('utf-8')


def make_k8s_secret(name, payload):
    """ Creates a K8S secret instance for pushing to the K8S API. """
    s = kubernetes.client.V1Secret()
    s.data = payload
    s.metadata = kubernetes.client.V1ObjectMeta()
    s.metadata.name = name
    return s


def push_k8s_secret(k8s_client, namespace, k8s_secret, do_nothing):
    """ Pushes a K8S secret instance to the API. """
    print('Pushing secret %s/%s' % (namespace, k8s_secret.metadata.name))
    if do_nothing:
        return
    try:
        k8s_client.replace_namespaced_secret(
            k8s_secret.metadata.name, namespace, k8s_secret)
    except kubernetes.client.rest.ApiException as e:
        print(e)
        if e.reason != 'Not Found':
            raise
        k8s_client.create_namespaced_secret(namespace, k8s_secret)


def delete_k8s_secret(k8s_client, namespace, name, do_nothing):
    """ Deletes a given (namespace, K8S secret name). """
    print('Deleting secret %s/%s' % (namespace, name))
    if do_nothing:
        return
    body = kubernetes.client.V1DeleteOptions()
    k8s_client.delete_namespaced_secret(name, namespace, body=body)


def sync_secrets(secrets_dir, k8s_client, do_nothing):
    """ Syncs a directory of KMS encrypted secrets to the current
    Kubernetes cluster. Specifically:

        - all secrets specified in the directory will be created or
          updated
        - all namespaces specified in the directory will be updated,
          such that only the secrets named in these directories are
          present
        - all namespaces not specified in the directory will be left
          alone.

    """
    if not os.path.isdir(secrets_dir):
        raise Exception(
            'Error: %s does not exist' % secrets_dir
        )

    root = os.path.normpath(secrets_dir)
    cluster_name = os.path.basename(root)
    check_cluster_name(cluster_name)

    root_depth = root.count('/')
    expected_secrets = set()
    for dirpath, dirnames, filenames in os.walk(root):
        depth = dirpath.count('/') - root_depth
        if depth == 2:
            _, namespace, secret_name = dirpath.rsplit('/', 2)
            secret_payload = {}
            for fname in filenames:
                path = os.path.join(dirpath, fname)
                plaintext = read_ciphertext(path)
                secret_payload[fname] = encode_payload(plaintext)
            k8s_secret = make_k8s_secret(secret_name, secret_payload)
            push_k8s_secret(
                k8s_client, namespace, k8s_secret, do_nothing
            )
            expected_secrets.add((namespace, secret_name))
        elif depth > 2:
            raise Exception('Unexpected directory depth: %s' % dirpath)

    expected_namespaces = set(t[0] for t in expected_secrets)

    all_secrets = k8s_client.list_secret_for_all_namespaces().items

    service_account_secrets = set(
        (s.metadata.namespace, s.metadata.name) for s in
        all_secrets if s.type == 'kubernetes.io/service-account-token'
    )

    actual_secrets = set(
        (s.metadata.namespace, s.metadata.name) for s in
        all_secrets
    )
    actual_namespaces = set(t[0] for t in actual_secrets)

    unexpected_secrets = actual_secrets - expected_secrets
    unexpected_namespaces = actual_namespaces - expected_namespaces

    untracked_secrets = set(
        t for t in unexpected_secrets if t[0] in unexpected_namespaces
    )
    untracked_secrets = untracked_secrets.union(service_account_secrets)
    secrets_to_delete = set(
        t for t in (unexpected_secrets - untracked_secrets)
    )

    if untracked_secrets:
        print("Secrets we don't track:")
        print(
            '\n'.join(
                '    %s/%s' % t for t in sorted(untracked_secrets)
            )
        )
        print()

    if secrets_to_delete:
        for namespace, secret_name in sorted(secrets_to_delete):
            delete_k8s_secret(
                k8s_client,
                namespace,
                secret_name,
                do_nothing
            )


if __name__ == '__main__':
    args = parser.parse_args()

    kubernetes.config.load_kube_config()
    k8s_client = kubernetes.client.CoreV1Api()
    sync_secrets(
        args.cluster_secrets_dir,
        k8s_client,
        args.do_nothing,
    )
