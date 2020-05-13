import os
import jinja2
import falcon


class TemplateResource(object):
    """
    Serves HTML templates. Note that templates are read from the FS for
    every request.
    """

    def __init__(self, template_dir, context=None):
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir),
            autoescape=jinja2.select_autoescape(['html']),
        )
        if context is not None:
            self.context = context
        else:
            self.context = {}

    def render_template(self, resp, tname):
        tname = to_template_names(tname)
        try:
            template = self.env.select_template(tname)
            resp.body = template.render(**self.context)
            resp.content_type = 'text/html'
        except jinja2.TemplateNotFound:
            resp.status = falcon.HTTP_404
            return

    def on_get(self, req, resp):
        self.render_template(resp, req.path)


def to_template_names(path):
    """
    Maps HTTP request paths to Jinja template paths.

    Args:
        path: path portion of HTTP GET request

    Returns:
        Tuple of file paths that Jinja should search for.
    """

    if not path.startswith('/'):
        raise ValueError
    path = path[1:]  # remove leading /, jinja won't want it

    if os.path.basename(path).startswith('_'):
        # Macros are kept in templates starting with _; don't allow
        # access to them.
        return tuple()

    if path == '':
        return ('index.html',)

    if path.endswith('/'):
        return (
            path[:-1] + '.html',
            os.path.join(path, 'index.html'),
        )

    if path.endswith('.html'):
        return (
            path,
            os.path.join(path[:-5], 'index.html'),
        )

    return (
        path + '.html',
        os.path.join(path, 'index.html'),
    )
