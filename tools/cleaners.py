# # -*- coding: utf-8 -*-
import re


def clean_html(raw_html):
    """Remove HTML tags from scrapped HTML."""
    regex = re.compile(u'<.*?>')
    clean_text = re.sub(regex, '', raw_html)
    return clean_text
