"""
This code lets you run the reference parser with the
latest scraped documents for an input organisations.
e.g.
python parse_latest.py msf
which will parse and match the latest msf scrape in S3
with the uber wellcome publications stored in S3
"""

from argparse import ArgumentParser
from urllib.parse import urlparse
import os
import logging

import boto3

from .refparse import parse_references, create_argparser
from .settings import settings

parser = ArgumentParser(description=__doc__.strip())

ORG_NAMES = (
    'gov_uk',
    'msf',
    'nice',
    'parliament',
    'unicef',
    'who_iris'
)

if __name__ == "__main__":
    logger = settings.logger
    logger.setLevel(logging.INFO)

    parser = create_argparser(__doc__.strip())
    parser.add_argument('org_name', choices=ORG_NAMES)

    args = parser.parse_args()
    org = args.org_name

    s3prefix = os.path.join(settings.SCRAPER_RESULTS_BASEDIR, org)
    u = urlparse(s3prefix)
    bucket_name, prefix = u.netloc, u.path[1:]

    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucket_name)

    # Get the most recently scraped filename
    key_name, obj = max(
        (obj.key, obj) for obj in bucket.objects.filter(Prefix=prefix).all()
    )

    if args.output_url.startswith('file://'):
        # The output subfolder will be the name of the organisation 
        # and the date of scrape (which is the name of the file)
        output_url = '{}/{}_{}'.format(
            args.output_url,
            org,
            os.path.splitext(os.path.basename(key_name))[0]
        )
        if not os.path.exists(output_url[7:]):
            os.makedirs(output_url[7:])

        scraper_file = "s3://{}/{}".format(bucket_name, key_name)

        parse_references(
            scraper_file,
            args.references_file,
            args.model_file,
            output_url,
            args.num_workers,
            logger
            )
    else:
        logger.info("Output url should start with 'file://'")
        pass
