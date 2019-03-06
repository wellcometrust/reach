"""
Parse a set of pdfs from a given directory to extract their text, sections and
find some words with their context.
"""
import os
import logging
from scraper.wsf_scraping.storage import S3Storage, LocalStorage
from urllib.parse import urlparse
from argparse import ArgumentParser
from pdf_parser.pdf_parse import parse_pdf_document, grab_section

logger = logging.getLogger(__name__)
logger.setLevel('INFO')


def write_to_file(output_url, item):
    """Write the results of the parsing in an output file.

    Args:
        output_url: The file to write the results to.
        item: A dictionnary containing the results of the parsing for a pdf.
    """
    return


def run_parsing(pdf, words, titles, context):
    """Parse the given pdf and returns a dict containing its test, sections and
       keywords.

    Args:
        pdf: A pdf file binary.
        words: A list of words to look for.
        titles: A list containing the titles of the sections to look for.
    Return:
        item: A dict containing the pdf text, sections and keywords.
    """
    # Convert PDF content to text format
    with open(pdf, 'rb') as f:

        pdf_file, pdf_text = parse_pdf_document(f)
        # If the PDF couldn't be converted, still remove the pdf file
        if not pdf_file:
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
                section_dict[title.title()] = section

    return {
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
        help='URL (local://! | s3://!)',
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


if __name__ == '__main__':

    parser = create_argparser(description=__doc__.strip())
    args = parser.parse_args()

    keywords_file = os.path.join(args.resource_file, 'keywords.txt')
    sections_file = os.path.join(args.resource_file, 'section_keywords.txt')

    # Get the sections and keywords to look for.
    words = parse_keywords_files(keywords_file)
    titles = parse_keywords_files(sections_file)

    parsed_url = urlparse(args.input_url)
    if parsed_url.scheme == 's3':
        storage = S3Storage(args.output_url, args.organisation)
    else:
        storage = LocalStorage(args.output_url, args.organisation)

    parsed_items = []
    for directory in storage.get_manifest():
        for item in directory:
            pdf = storage.get(item)
            item = run_parsing(
                pdf,
                words,
                titles,
                args.keywords_search_context
            )
            parsed_items.append(item)

    write_to_file(parsed_items)
