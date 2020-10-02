""" Serve GET /robots.txt. """

# Allow all indexing following launch in July 2020
# (cf.
# https://medium.com/wellcome-data-labs/introducing-reach-find-and-track-research-being-put-into-action-dec2a2fca93b)
ROBOTS_TXT = \
"""User-agent: *
Allow: /
"""

class RobotsTxtResource(object):
    def on_get(self, req, resp):
        resp.body = ROBOTS_TXT
        resp.content_type = 'text/plain'
