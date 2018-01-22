# # -*- coding: utf-8 -*-
import re


def clean_html(raw_html):
    """Remove HTML tags from scrapped HTML."""
    regex = re.compile(u'<.*?>')
    clean_text = re.sub(regex, '', raw_html)
    return clean_text


def parse_keywords_files(file_path):
    """Convert keyword files into lists, ignoring # commented lines."""
    keywords_list = []
    with open(file_path, 'r') as f:
        for line in f:
            line = line.replace('\n', '')
            if line and line[0] != '#':
                keywords_list.append(line.lower())
    return keywords_list
