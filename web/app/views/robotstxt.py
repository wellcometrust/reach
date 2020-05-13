""" Serve GET /robots.txt. """

# Disable all indexing until beta.
ROBOTS_TXT = \
"""User-agent: *
Disallow: /
"""

class RobotsTxtResource(object):
    def on_get(self, req, resp):
        resp.body = ROBOTS_TXT
        resp.content_type = 'text/plain'
