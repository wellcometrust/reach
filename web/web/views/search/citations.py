import logging
import json

import falcon

from web.db import get_db_cur
from web.views import template

logger = logging.getLogger(__name__)

class SearchCitations(template.TemplateResource):
    """ Search through publications returning a list of publications with inlined policies that have cited
    the publication, search rank.
    """
    def __init__(self, template_dir, context=None):
        super(SearchCitations, self).__init__(template_dir, context)

    def on_get(self, req, resp):
        logger.info("Requesting some citations")

        if not req.params:
            super(SearchCitations, self).render_template(
                resp,
                "/search/citations",
            )
            return

        term = req.params.get("terms", "")

        self.context.update(dict(
            term=term
        ))

        super(SearchCitations, self).render_template(
            resp,
            "/results/citations",
        )


