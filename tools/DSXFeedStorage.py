import json
import logging
import requests
import posixpath
from scrapy.utils.boto import is_botocore
from six.moves.urllib.parse import urlparse
from scrapy.extensions.feedexport import BlockingFeedStorage


class DSXFeedStorage(BlockingFeedStorage):

    def __init__(self, uri):
        from scrapy.conf import settings
        u = urlparse(uri)
        self.file_name = u.path[1:]
        self.storage_name = settings['DSX_FEED_CONTAINER']
        self.credentials = settings['DSX_CREDENTIALS']
        self.auth_url = settings['DSX_AUTH_URL']

    def _store_in_thread(self, file):
        file.seek(0)

        url = "https://identity.open.softlayer.com/v3/auth/tokens"

        headers = {
            'Content-Type': "application/json",
            'Cache-Control': "no-cache",
        }
        data = json.dumps({
            "auth": {
                "identity": {
                    "methods": ["password"],
                    "password": {
                        "user": {
                            "name": self.credentials['username'],
                            "domain": {
                                "id": self.credentials['domainId']
                            },
                            "password": self.credentials['password']
                        }
                    }
                }
            }
        })

        headers1 = {'Content-Type': 'application/json'}
        resp1 = requests.post(
            url=url,
            data=data,
            headers=headers
        )
        resp1_body = resp1.json()
        for e1 in resp1_body['token']['catalog']:
            if(e1['type'] == 'object-store'):
                for e2 in e1['endpoints']:
                    if(e2['interface'] == 'public' and
                       e2['region'] == self.credentials['region']):
                        url2 = ''.join(
                            [
                                e2['url'],
                                '/',
                                self.storage_name,
                                '/',
                                self.file_name
                            ]
                        )

        s_subject_token = resp1.headers['x-subject-token']
        headers2 = {
            'X-Auth-Token': s_subject_token,
            'accept': 'application/json'
        }
        file_content = file.read()
        resp2 = requests.put(url=url2, headers=headers2, data=file_content)
        logging.debug("Stored the file in: %s" % url2)
