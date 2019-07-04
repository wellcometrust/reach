"""
Parse a set of pdfs from a given directory to extract their text, sections and
find some words with their context.
"""
from urllib.parse import urlparse
from argparse import ArgumentParser
import os
import logging
import tempfile
import json

from policytool.scraper.wsf_scraping.file_system import (
    S3FileSystem,
    LocalFileSystem
)
from policytool.pdf_parser.pdf_parse import parse_pdf_document, grab_section

logger = logging.getLogger(__name__)
logger.setLevel('INFO')


def write_to_file(output_url, items, organisation):
    """Write the results of the parsing in an output file.

    Args:
        output_url: The file to write the results to.
        item: A dictionnary containing the results of the parsing for a pdf.
    """
    parsed_url = urlparse(output_url)
    if parsed_url.scheme == 'manifests3':
        file_system = S3FileSystem(
            parsed_url.path,
            organisation,
            parsed_url.netloc
        )
    else:
        file_system = LocalFileSystem(
            parsed_url.path,
            organisation)
    key = 'policytool-parse--parser-{org}.json'.format(org=organisation)
    file_system.save(json.dumps(items), '', key)


def parse_pdf(pdf, words, titles, context, pdf_hash):
    """Parse the given pdf and returns a dict containing its test, sections and
       keywords.

    Args:
        pdf: A pdf file binary.
        words: A list of words to look for.
        titles: A list containing the titles of the sections to look for.
        context: The number of lines to scrape before and after a keyword.
        pdf_hash: The pdf md5 digest.
    Return:
        item: A dict containing the pdf text, sections and keywords.
    """
    # Convert PDF content to text format
    with open(pdf, 'rb') as f:

        pdf_file, pdf_text = parse_pdf_document(f)
        # If the PDF couldn't be converted, still remove the pdf file
        if not pdf_file:
            logger.warning('The pdf couldn\'t be parsed {pdf_hash}'.format(
                pdf_hash=pdf_hash,
            ))
            return None

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
                if section_dict.get(title.title()):
                    section_dict[title.title()].append(section)
                else:
                    section_dict[title.title()] = [section]

    return {
        'file_hash': pdf_hash,
        'sections': section_dict,
        'keywords': keyword_dict,
        'text': pdf_text
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


def create_argparser(description):
    """Create the argument parser for this module.

    Args:
        description: The module description.
    Returns:
        parser: The argument parser from this configuration.
    """
    parser = ArgumentParser(description)
    parser.add_argument(
        '--input-url',
        help='Path or S3 URL to the manifest file.',
        default=os.environ['PDF_PARSER_INPUT_URL']
    )

    parser.add_argument(
        '--output-url',
        help='URL (local://! | manifests3://!)',
        default=os.environ['PDF_PARSER_OUTPUT_URL']
    )

    parser.add_argument(
        '--resource-files',
        help='Path to the keyword and section titles files',
        default=os.environ['PDF_PARSER_resources']
    )

    parser.add_argument(
        '--keyword-search-context',
        help='Number of lines to save before and after finding a word.',
        default=os.environ['PDF_PARSER_CONTEXT'],
        type=int
    )

    parser.add_argument(
        '--organisation',
        help='The orgnasition to scrape: [who_iris|nice|gov_uk|msf|unicef'
             '|parliament]',
    )

    return parser


def parse_all_pdf(input_url, output_url, resource_file, organisation, context):
    """Parses all the pdfs from the manifest in the input url and export the
    result to the ouput url.

    This method will get the manifest file located at the input url, and
    iterate through it to:
      * Dowload the pdf to a temporary file.
      * Convert it to xml using the parse_pdf method to get its text, sections
        and keywords, with the given number of context lines.
      * Save the output to a json file located at the given output_url.

    Args:
        input_url: The location where the entry manifest file is located.
        output_url: The location to put the file containing the parsed items.
        resource_file: The location to find the files containing the titles
                       and words to look for.
        orgnaisation: The organisation to parse the files from.
        context: The number of lines to save before and after finding a word
                 from the keywords list.
    """
    logger.info(output_url)
    keywords_file = os.path.join(resource_file, 'keywords.txt')
    sections_file = os.path.join(resource_file, 'section_keywords.txt')

    # Get the sections and keywords to look for.
    words = parse_keywords_files(keywords_file)
    titles = parse_keywords_files(sections_file)

    parsed_url = urlparse(input_url)
    if parsed_url.scheme == 'manifests3':
        file_system = S3FileSystem(
            parsed_url.path,
            organisation,
            parsed_url.netloc,
        )
    else:
        file_system = LocalFileSystem(output_url, organisation)

    parsed_items = []
    manifest = file_system.get_manifest()
    for directory in manifest:
        for item in manifest[directory]:
            pdf = file_system.get(item)

            # Download PDF file to /tmp
            with tempfile.NamedTemporaryFile(delete=False) as tf:
                tf.write(pdf.read())
                tf.seek(0)
                item = parse_pdf(
                    tf.name,
                    words,
                    titles,
                    context,
                    item,
                )
            parsed_items.append(item)

    write_to_file(output_url, json.dumps(parsed_items), organisation)


if __name__ == '__main__':

    parser = create_argparser(description=__doc__.strip())
    args = parser.parse_args()

    parse_all_pdf(
        args.input_url,
        args.output_url,
        args.resource_file,
        args.organisation,
        args.keywords_search_context,
    )
