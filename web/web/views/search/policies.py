import logging
import json

import falcon

from web.views import template

logger = logging.getLogger(__name__)

class SearchPolicies(template.TemplateResource):
    """ Search through publications returning a list of publications with inlined policies that have cited
    the publication, search rank.
    """
    def __init__(self, template_dir, context=None):
        super(SearchPolicies, self).__init__(template_dir, context)

    def on_get(self, req, resp):
        logger.info("Requesting some policies")

        if not req.params:
            super(SearchPolicies, self).render_template(
                resp,
                "/search/policy-docs",
            )
            return

        term = req.params.get("terms", None)

        self.context.update(dict(
            term=term
        ))

        super(SearchPolicies, self).render_template(
            resp,
            "/results/policy-docs",
        )


