"""
Operator for normalizing the name coming from the PDF
"""

import json
import logging
import tempfile
import gzip
import os

from hooks.sentry import report_exception
from hooks.s3hook import S3Hook

logger = logging.getLogger(__name__)


class PolicyNameCandidates(object):
    """ Represents all the candidates from a given doc
    that could potentially be the title
    """

    def __init__(self, doc):
        pdf_meta = doc.get("pdf_metadata", {})
        source_meta = doc.get("source_metadata", {})
        # Title pulled from the pdfs metadata object
        self.pdf_metadata_title = pdf_meta.get("title", None)
        # Title pulled from a variety of sources, a heading link the
        # pdf was downloaded from. Or known correlating title item in the page.
        # If this exists it might be best to give it a higher priority.
        self.source_title = source_meta.get("title", None)
        # Title pulled from the download page
        self.source_page_title = source_meta.get("page_title", None)
        # Text pulled from the link the fiel was downloaded from
        self.link_title = source_meta.get("link_title", None)
        # The actual filename for the file (based on download URL)
        self.filename = source_meta.get("url_filename", None)
        # The Content-Disposition header name/filename attribute
        self.disposition_title = source_meta.get("disposition_title", None)

        # text lines in PDF, sorted by font size, popping the first three
        self.pdf_title_candidates = doc.get("title_candidates", [])
        # Heading from the source page that the pdf was downloaded from
        self.page_headings = source_meta.get("page_headings", [])

    def get_title(self):
        """ Really basic temporary tackling at this point
        to decide which one of these should be used
        """
        if self.source_title:
            return self.source_title

        if len(self.pdf_title_candidates) > 0:
            return self.pdf_title_candidates[0]

        if len(self.page_headings) > 0:
            return self.page_headings[0]


class PolicyNameNormalizerOperator(object):
    """
    Pulls data from after the PDF has been parsed in order
    to evaluate and weight potential titles for the policy
    from different sources resulting in a single canonical
    policy title.

    Should discard all other title candidates.

    Args:
        organisation: The organisation to pull documents from.
    """

    def __init__(self, organisation, src_s3_key, dst_s3_key):
        # XXX: This is currently a dummy placeholder, it's output is the
        # same as it's input until this operator is wired up.
        self.src_s3_key = src_s3_key
        self.dst_s3_key = os.path.join(
            dst_s3_key,
            'policy_docs_normalized.json.gz',
        )

    @report_exception
    def normalize(self):
        # Initialise settings for a limited scraping
        logger.info("Deciding on policy title")
        s3 = S3Hook()

        results = []

        with tempfile.TemporaryFile(mode='rb+') as tf:
            key = s3.get_s3_object(self.src_s3_key)
            key.download_fileobj(tf)
            tf.seek(0)
            with gzip.GzipFile(mode='rb', fileobj=tf) as f:
                for line in f:
                    data = json.loads(line)
                    source_meta = data.get("source_metadata", {})
                    pdf_meta = data.get("pdf_metadata", {})
                    p_name = PolicyNameCandidates(data)
                    results.append(json.dumps({
                        'file_hash': data.get("file_hash"),
                        'keywords': data.get('keywords', {}),
                        'text': data.get('text', ''),
                        'sections': data.get('sections', []),
                        'url': source_meta.get("url", None),
                        'source_page': source_meta.get('source_page', None),
                        'title': p_name.get_title(),
                        'authors': source_meta.get("authors", None),
                        'year': source_meta.get("year", None),
                        'subjects': source_meta.get("subjects", None),
                        'created': pdf_meta.get("created", None),
                        'types': source_meta.get("types", None)
                    }))
        # Write the results to S3
        with tempfile.NamedTemporaryFile(mode='wb') as output_raw_f:
            with gzip.GzipFile(mode='wb', fileobj=output_raw_f) as output_f:
                for item in results:
                    output_f.write(item.encode("utf-8"))
                    output_f.write(b"\n")

            output_raw_f.flush()
            s3.load_file(
                output_raw_f.name,
                self.dst_s3_key,
                replace=True
            )
            logger.info(
                'PolicyNameNormalizerOperator: Done normalizing policy names'
            )
