# # -*- coding: utf-8 -*-

import hashlib
import logging


def parse_keywords_files(file_path):
    """Convert keyword files into lists, ignoring # commented lines."""
    logger = logging.getLogger(__name__)
    logger.debug("Try to open keyword files")
    keywords_list = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            logger.debug("Successfully opened %s", file_path)
            for line in f:
                line = line.replace('\n', '')
                if line and line[0] != '#':
                    keywords_list.append(line.lower())
    except IOError:
        logger.warning(
            "Unable to open keywords file at location %s", file_path
        )
        keywords_list = []
    finally:
        return keywords_list


def get_file_hash(file_path):
    """Return the md5 hash of a file."""
    BLOCKSIZE = 65536
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        while True:
            buf = f.read(BLOCKSIZE)
            if not buf:
                break
            hasher.update(buf)
    return hasher.hexdigest()
