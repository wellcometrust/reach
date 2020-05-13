from reach.web.views import template


def test_to_template_names():
    cases = [
        ('/', ('index.html',)),
        ('/foo', ('foo.html', 'foo/index.html')),
        ('/foo.html', ('foo.html', 'foo/index.html')),
        ('/foo/gar', ('foo/gar.html', 'foo/gar/index.html')),
        ('/_macros.html', tuple()),
    ]
    for path, expected in cases:
        assert expected == template.to_template_names(path)
