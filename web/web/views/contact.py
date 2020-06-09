import logging
import json
import uuid
import datetime
import re

import requests
from requests.auth import HTTPBasicAuth
import falcon

from web.views import template
from web.utils import rate_limit
from web import config as conf

logger = logging.getLogger(__name__)

ISSUE_BODY = """

Name: {}
Email: {}
Message:

{}

Received: {}
"""

GITHUB_ENDPOINT = "https://api.github.com/repos/wellcometrust/datalabs-support/issues"

FORM_SCHEMA = {
        'name': {'type': 'string', "required": True},
        'email': {'type': "email", "required": True},
        'comment': {'type': "string", "required": True},
        "ck_erp_val": {"type": "string", "required": True},
        "nonce": {"type": "string", "required": True}
}

EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")

def submit_issue(name, email, comment):

    if not conf.CONFIG.github_token:
        raise Exception("GITHUB_TOKEN has not been specified")
        return False

    now = datetime.datetime.utcnow()
    content = ISSUE_BODY.format(
        name,
        email,
        comment,
        now.strftime("%Y-%m-%d"),
    )

    r = requests.post(GITHUB_ENDPOINT, json={
            'title': "New Contact Submission: %s" % (email,),
            'body':  content,
            'labels': ["Contact"]
        },
        auth=HTTPBasicAuth(conf.CONFIG.github_user, conf.CONFIG.github_token)
    )


    if r.status_code == 201:
        return True
    else:
        logging.error("An error occured creating the GitHub issue")
        return False


class ContactView(template.TemplateResource):
    """ Contact form view for the application
    """
    def __init__(self, template_dir, context=None):
        context = context
        super(ContactView, self).__init__(template_dir, context)

    def on_get(self, req, resp):
        cookie_val = str(uuid.uuid4())

        resp.set_cookie("__xsrf", cookie_val)

        self.context.update({"ck_val": cookie_val})
        super(ContactView, self).render_template(
            resp,
            "/contact",
        )

    @falcon.before(rate_limit(per_second=1, window_size=60*60, resource='contact'))
    def on_post(self, req, resp):
        cookies = req.cookies
        ck_val = None
        if "__xsrf" in cookies:
            ck_val = cookies['__xsrf']
        else:
            logging.info("__xsrf cookie is missing")
            resp.status = falcon.HTTP_400
            return

        if ck_val in (None, ''):
            logging.info("_xsrf cookie value is empty is missing")
            resp.status = falcon.HTTP_400
            return

        data = req.media

        if data is None:
            logging.info("No data in payload")
            resp.status = falcon.HTTP_400
            return

        if data.get("ck_erp_val") != ck_val:
            logging.info("__xsrf cookie non-match")
            resp.status = falcon.HTTP_400
            return

        if data.get("anchor", "").strip() != "":
            resp.status("nonce was entered: Bot Alert")
            resp.status = falcon.HTTP_400
            return

        if data.get("name", None) in (None, ""):
            resp.body = json.dumps({
                "success": False,
                "err": "ERR_NO_NAME"
            })
            return

        email = data.get("email", None)
        if email in (None, ""):
            resp.body = json.dumps({
                "success": False,
                "err": "ERR_NO_EMAIL"
            })
            return

        # TODO: If we want to get crazy we can potentially poll the SMTP
        # server to check the emails valid and have a bit more complex logic here
        if not EMAIL_REGEX.match(email):
            resp.body = json.dumps({
                "success": False,
                "err": "ERR_NO_EMAIL"
            })
            return

        if data.get("comment", None) in (None, ""):
            resp.body = json.dumps({
                "success": False,
                "err": "ERR_NO_COMMENT"
            })
            return



        # TODO: Validate

        issue_result = submit_issue(
            data.get("name"),
            data.get("email"),
            data.get("comment"),
        )

        if issue_result:
            resp.body = json.dumps(dict(
                success=True
            ))
        else:
            resp.body = json.dumps(dict(
                success=False,
                err="GH_SUBMIT_FAILED"

            ))


