#!/usr/bin/env python3

"""
Prints the environment variables used for developing in this repo,
after decrypting them using AWS KMS.
Depends on `aws` (from awscli) being in your path, but not boto3.
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
import configparser

parser = ArgumentParser(description=__doc__.strip())
parser.add_argument('-r', dest='raw', action='store_true',
                    help='Print raw plaintext instead of removing \\s')

CIPHERTEXT_BLOB = "AQICAHhguvwpM7IxTcll8NLhRiUH41+cNUymMx+YBOtLWUn7ogGyCOeYnH+HdZOq0nCQY159AAABZDCCAWAGCSqGSIb3DQEHBqCCAVEwggFNAgEAMIIBRgYJKoZIhvcNAQcBMB4GCWCGSAFlAwQBLjARBAwt4TsxrEXrc5fqTcUCARCAggEXpcs6/PuMMjusKgfCGt0KHYvm4kSTXtk3TkTsL2gxyr9+lBpHocuktzYrQo3gjagaBEms25yk2eW26BnNfjp0NooAYDlBM9TrMeCke67ulH/NqnN6vCXuHzAdBPTKY/bMddE34Rs7B8rWy9qivQqPuI7AaxIQ/o58Knx3i+2fl9uph6PVZ+sC13MSQV/r8KmmOl2AfMZKUd/KHRiB1HA3Q3ywhnAYM3bh5jaD2I7oYKXQCuY6Q1tUNpU34qJLRPX7jC8dT/daRj97aMAqo2M4DYb/RQNQIed5lba67ljS9Qx4Lj3Drba9r8rd4W0lfw6ftnt9uify2zdtLzajhRSfNambyDolNyYeBV8k1KLHr85/jKaKad2W"


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


def aws_creds_to_env():
    env = 'export '
    conf = configparser.ConfigParser()
    conf.read('/Users/depardieus/.aws/credentials')
    for i in conf['default']:
        if i.startswith('aws'):
            env += '{}={} '.format(i.upper(), conf['default'][i])

    return env


if __name__ == '__main__':
    args = parser.parse_args()
    env = decrypt_env()
    if not os.environ.get('AWS_ACCESS_KEY_ID'):
        if not env.endswith(';'):
            env += ';'
        env += aws_creds_to_env()
    if not args.raw:
        # $(./export_env.py) fails unless we strip out \'s
        env = env.replace('\\', '')
sys.stdout.write(env)
