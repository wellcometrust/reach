"""
Common logging setup for Reach services.
"""

import logging

def basicConfig(level=logging.INFO):
    """ Configure stderr logging w/ISO8601 prefix. """
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=level,
        datefmt='%Y-%m-%d %H:%M:%S')

