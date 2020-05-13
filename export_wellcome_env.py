#!/usr/bin/env python3

"""
Prints environment variables that are not required, but that can help
Wellcome employees when developing in this repo. (Only one variable is
provided just now: SENTRY_DSN, so that exceptions in localdev can be
inspected from the Sentry UI.)

Depends on:

    - `aws` (from awscli) being in your path, but not boto3.
    - Wellcome AWS credentials that support decrypting the ciphertext
      below.

NB: to update the ciphertext:
```
export_env.py -r > /tmp/creds.sh
vi /tmp/creds.sh
aws kms encrypt --key-id alias/localdev-datalabs --plaintext fileb:///tmp/creds.sh
```
"""

from argparse import ArgumentParser
import base64
import json
import subprocess
import sys
import os
import os.path
import configparser

parser = ArgumentParser(description=__doc__.strip())
parser.add_argument('-r', dest='raw', action='store_true',
                    help='Print raw plaintext instead of removing \\s')

CIPHERTEXT_BLOB = "AQICAHhguvwpM7IxTcll8NLhRiUH41+cNUymMx+YBOtLWUn7ogHC88/HvpfVAu7FXCAC+54sAAAAsTCBrgYJKoZIhvcNAQcGoIGgMIGdAgEAMIGXBgkqhkiG9w0BBwEwHgYJYIZIAWUDBAEuMBEEDD4FDbBSWOIWi5aNEgIBEIBq6uGSuXJ/Jy2cwwC/2KMj/nhvurBbDIL2Q9dIgg9ye/yZR4eGrcGgAOC0iQ58oTJl6F4xhcFk74DFj3xrFiOpK68Ym+bGq4Zre4lHzQYPY4RDr0CHv8Bqy65Pe0GGnF/agmRRwlbDirzcAw=="


def decrypt_env():
    """ Returns plaintext of CIPHERTEXT_BLOB for use in the shell. """
    raw = base64.b64decode(CIPHERTEXT_BLOB)
    p = subprocess.Popen(
        ['aws', 'kms', 'decrypt', '--output', 'json',
            '--ciphertext-blob', 'fileb:///dev/stdin'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE
    )
    out, _ = p.communicate(raw)
    if p.returncode != 0:
        raise Exception('Error running aws kms decrypt')
    d = json.loads(out)
    return base64.b64decode(d['Plaintext']).decode('utf8')


def add_cred_to_secrets(cred, secret):
    with open('./argo/secrets/minikube/argo/aws/{}'.format(cred.lower()),
              'wb') as f:
        f.write(base64.b64encode(secret.encode('utf8')))


def aws_creds_to_env():
    env = 'export '
    conf = configparser.ConfigParser()
    conf.read(os.path.expanduser('~/.aws/credentials'))
    for i in conf['default']:
        if i.startswith('aws'):
            env += '{}={} '.format(i.upper(), conf['default'][i])
            add_cred_to_secrets(i, conf['default'][i])
    return env


if __name__ == '__main__':
    args = parser.parse_args()
    env = decrypt_env()
    if not os.environ.get('AWS_ACCESS_KEY_ID'):
        if not env.endswith(';'):
            env += ';'
        env += aws_creds_to_env()
    else:
        add_cred_to_secrets(
            "AWS_ACCESS_KEY_ID".lower(),
            os.environ.get("AWS_ACCESS_KEY_ID")
        )
        add_cred_to_secrets(
            "AWS_SECRET_ACCESS_KEY".lower(),
            os.environ.get("AWS_SECRET_ACCESS_KEY")
        )
    if not args.raw:
        # $(./export_env.py) fails unless we strip out \'s
        env = env.replace('\\', '')
sys.stdout.write(env)
