"""
Parse a set of pdfs from a given directory to extract their text, sections and
find some words with their context.

Example:

    python -m reach.pdf_parser.main \
      msf \
      s3://datalabs-staging/reach-airflow/output/policy/spider/msf/spider-msf \
      s3://datalabs-dev/pdf_parser_test_output.json.gz


"""
from argparse import ArgumentParser
from urllib.parse import urlparse, urljoin
import gzip
import json
import logging
import os
import os.path
import shutil
import tempfile

from hooks.s3hook import S3Hook
from .pdf_parse import parse_pdf_document, grab_section

logger = logging.getLogger(__name__)

KEYWORD_SEARCH_CONTEXT = 2


def default_resources_dir():
    """ Returns path to resources/ within our repo. """
    return os.path.join(
        os.path.dirname(__file__),
        'resources'
    )


def write_to_file(output_url, items, organisation):
    """Write the results of the parsing in an output file.

    Args:
        output_url: The file to write the results to.
        item: A dictionnary containing the results of the parsing for a pdf.
    """
    parsed_url = urlparse(output_url)
    fname = os.path.basename(parsed_url.path)
    s3_hook = S3Hook()
    if fname.endswith('.json.gz'):
        with tempfile.TemporaryFile(mode='w+b') as raw_f:
            with gzip.GzipFile(fileobj=raw_f, mode='w') as f:
                # No text mode GzipFile until Python 3.7 :-(
                for item in items:
                    f.write(json.dumps(item).encode('utf-8'))
                    f.write(b"\n")
            raw_f.flush()
            raw_f.seek(0)
            s3_hook.save_fileobj(raw_f, output_url)
    else:
        raise ValueError(
            'Unsupported output_url: %s' % output_url)


def parse_pdf(pdf, words, titles, context, pdf_hash, metadata):
    """Parse the given pdf and returns a dict containing its test, sections and
       keywords.

    Args:
        pdf: file object, pointing to a named file
        words: A list of words to look for.
        titles: A list containing the titles of the sections to look for.
        context: The number of lines to scrape before and after a keyword.
        pdf_hash: The pdf md5 digest.
    Return:
        item: A dict containing the pdf text, sections and keywords.
    """
    # Convert PDF content to text format
    pdf_file, pdf_text, pdf_metadata, errors = parse_pdf_document(pdf)
    # If the PDF couldn't be converted, still remove the pdf file
    if not pdf_file:
        assert errors, 'Errors must be supplied if no parse'
        logger.warning(
            'parse_pdf: pdf_hash=%s errors=%s',
            pdf_hash, ','.join(errors)
        )

        # We still have to return something for the json to be complete.
        return {
            'file_hash': pdf_hash,
            'sections': None,
            'keywords': None,
            'text': None,
            'errors': errors,
        }

    # Fetch references or other keyworded list
    keyword_dict = pdf_file.get_lines_by_keywords(
        words,
        context
    )

    section_dict = {}
    for title in titles:
        # Fetch references or other keyworded list
        section = grab_section(pdf_file, title)

        # Add references and PDF name to JSON returned file
        # If no section matchs, leave the attribute undefined
        if section:
            if section_dict.get(title):
                section_dict[title].append(section)
            else:
                section_dict[title] = [section]

    return {
        'file_hash': pdf_hash,
        'sections': section_dict,
        'keywords': keyword_dict,
        'text': pdf_text,
        'pdf_metadata': pdf_metadata,
        'source_metadata': metadata,
        'title_candidates': pdf_file.get_title_candidates()
    }


def parse_keywords_files(file_path):
    """Convert keyword files into lists, ignoring # commented lines.

    Args:
        file_path: The absolute path to a word|title file to use.
    Returns:
        keywords_list: A list of words|titles to look for in the documents.
    """
    logger.debug("Try to open keyword files")
    keywords_list = []
    with open(file_path, 'r', encoding='utf-8') as f:
        logger.debug("Successfully opened %s", file_path)
        for line in f:
            line = line.replace('\n', '')
            if line and line[0] != '#':
                keywords_list.append(line.lower())
        return keywords_list


def create_argparser(description):
    """Create the argument parser for this module.

    Args:
        description: The module description.
    Returns:
        parser: The argument parser from this configuration.
    """
    parser = ArgumentParser(description)

    parser.add_argument(
        'organisation',
        help='The organisation that was scraped: '
             '[who_iris|nice|gov_uk|msf|unicef|parliament]',
    )

    parser.add_argument(
        'input_url',
        help='URL to the manifest file (file://... | s3://...)',
    )

    parser.add_argument(
        'output_url',
        help='URL (file://... | s3://...)',
    )

    parser.add_argument(
        '--resources-dir',
        help='Path to dir containing keywords.txt & section_keywords.txt',
        default=default_resources_dir()
    )

    parser.add_argument(
        '--keyword-search-context',
        help='Number of lines to save before and after finding a word.',
        default=os.environ.get(
            'PDF_PARSER_CONTEXT', KEYWORD_SEARCH_CONTEXT),
        type=int
    )

    return parser


def _yield_items(s3_hook, words, titles, context, src_url, organisation):
    content = s3_hook.get_manifest(src_url, organisation)['content']
    # Load data about individual documents
    data = s3_hook.get_manifest(src_url, organisation)['data']

    # Create lookup dict for retrieving an individual docs information
    metadata_lookup = dict(
        (doc_id, metadata) for doc_id, metadata in data.items()
    )
    # Iterate through directories parsing individual PDFs
    for directory in content:
        for item in content[directory]:
            item_key = os.path.join(
                src_url,
                'pdf',
                item[:2],
                item + '.pdf'
            )
            logger.info(item_key + '  --- ' + directory)

            pdf = s3_hook.get(
                item_key
            )

            with tempfile.NamedTemporaryFile() as tf:
                shutil.copyfileobj(pdf, tf)
                tf.seek(0)
                yield parse_pdf(
                    tf,
                    words,
                    titles,
                    context,
                    item,
                    metadata_lookup.get(item, {})
                )


def parse_all_pdf(organisation, input_url, output_url,
                  context=KEYWORD_SEARCH_CONTEXT,
                  resources_dir=None):
    """Parses all the pdfs from the manifest in the input url and export the
    result to the ouput url.

    This method will get the manifest file located at the input url, and
    iterate through it to:
      * Dowload the pdf to a temporary file.
      * Convert it to xml using the parse_pdf method to get its text, sections
        and keywords, with the given number of context lines.
      * Save the output to a json file located at the given output_url.

    Args:
        organisation: The organisation to parse the files from.
        input_url: The location where the entry manifest file is located.
        output_url: The location to put the file containing the parsed items.
        context: The number of lines to save before and after finding a word
                 from the keywords list.
        resources_dir: Path to directory containing keywords.txt and
                       section_keywords.txt, used for finding titles and
                       words to look for.
    """
    logger.info(
        "parse_all_pdf: input_url=%s output_url=%s organisation=%s "
        "context=%d resources_dir=%s",
        input_url, output_url, organisation, context, resources_dir)
    if resources_dir is None:
        resources_dir = default_resources_dir()
    keywords_file = os.path.join(resources_dir, 'keywords.txt')
    sections_file = os.path.join(resources_dir, 'section_keywords.txt')

    # Get the sections and keywords to look for.
    words = parse_keywords_files(keywords_file)
    titles = parse_keywords_files(sections_file)

    s3_hook = S3Hook()
    parsed_items = _yield_items(s3_hook, words, titles, context,
                                input_url, organisation)

    write_to_file(output_url, parsed_items, organisation)


if __name__ == '__main__':
    import reach.logging
    reach.logging.basicConfig()

    parser = create_argparser(description=__doc__.strip())
    args = parser.parse_args()
    parse_all_pdf(
        args.organisation,
        args.input_url,
        args.output_url,
        args.keyword_search_context,
        resources_dir=args.resources_dir,
    )
