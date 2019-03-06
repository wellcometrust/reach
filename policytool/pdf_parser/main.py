"""
This is some dummy code to be replaced in the pdf parsing task.
"""

# from pdf_parser.pdf_parse import parse_pdf_document, grab_section
# from scraper.utils.dbTools import DatabaseConnector
# import os
# import datetime
# import logging
#
# logger = logging.getLogger(__name__)
# logger.setLevel('INFO')
#
#
# KEYWORDS_FILE = ''
# SECTIONS_KEYWORDS_FILE = ''
# KEYWORDS_CONTEXT = ''
#
#
# def parse_keywords_files(file_path):
#     """Convert keyword files into lists, ignoring # commented lines."""
#     logger = logging.getLogger(__name__)
#     logger.debug("Try to open keyword files")
#     keywords_list = []
#     try:
#         with open(file_path, 'r', encoding='utf-8') as f:
#             logger.debug("Successfully opened %s", file_path)
#             for line in f:
#                 line = line.replace('\n', '')
#                 if line and line[0] != '#':
#                     keywords_list.append(line.lower())
#     except IOError:
#         logger.warning(
#             "Unable to open keywords file at location %s", file_path
#         )
#         keywords_list = []
#     finally:
#         return keywords_list
#
#
# def check_keywords(self, item, spider_name, base_pdf_path):
#     """Convert the pdf file to a python object and analyse it to find
#     keywords and section based on the section/keywords files provided.
#     """
#
#     # Convert PDF content to text format
#     with open(item['pdf'], 'rb') as f:
#
#         logger.info(
#             'Processing: %s',
#             item['pdf']
#         )
#
#         pdf_file = parse_pdf_document(f)
#         # Get the sections and keywords to look for.
#         keywords = parse_keywords_files(
#             KEYWORDS_FILE
#         )
#         section_keywords = parse_keywords_files(
#             SECTIONS_KEYWORDS_FILE
#         )
#         # If the PDF couldn't be converted, still remove the pdf file
#         if not pdf_file:
#             os.remove(item['pdf'])
#             return item
#
#         for keyword in section_keywords:
#             # Fetch references or other keyworded list
#             section = grab_section(pdf_file, keyword)
#
#             # Add references and PDF name to JSON returned file
#             # If no section matchs, leave the attribute undefined
#             if section:
#                 item['sections'][keyword.title()] = section
#
#         # Fetch references or other keyworded list
#         keyword_dict = pdf_file.get_lines_by_keywords(
#             keywords,
#             KEYWORDS_CONTEXT
#         )
#
#         # Add references and PDF name to JSON returned file
#         # If no section matchs, leave the attribute undefined
#         if keyword_dict:
#             item['keywords'] = keyword_dict
#
#     # has_keywords = len(item['keywords'])
#
#     # If we need to keep the pdf, move it, else delete it
#     try:
#         os.unlink(item['pdf'])
#     except FileNotFoundError:
#         logger.warning(
#             "The file couldn't be found, and wasn't deleted."
#         )
#
#     # Remove the path from the value we are storing
#     item['pdf'] = os.path.basename(item['pdf'])
#     item['provider'] = spider_name
#     item['date_scraped'] = datetime.now().strftime('%Y%m%d')
#     item['has_text'] = True
#     return item
#
#
# if __name__ == '__main__':
#     item = {}
#     name = ''
#     scraped = False
#     database = DatabaseConnector()
#     if not scraped:
#         full_item = check_keywords(item, name, item['pdf'])
#
#         id_provider = database.get_or_create_name(
#             name, 'provider'
#         )
#         id_publication = database.insert_full_publication(
#             full_item,
#             id_provider
#         )
#         database.insert_joints_and_text(
#             'section',
#             full_item.get('sections'),
#             id_publication
#         )
#         database.insert_joints_and_text(
#             'keyword',
#             full_item.get('keywords'),
#             id_publication
#         )
#         database.insert_joints(
#             'type',
#             full_item.get('types'),
#             id_publication
#         )
#         database.insert_joints(
#             'subject',
#             full_item.get('subjects'),
#             id_publication
#         )
#
#     elif scraped.scrape_again:
#
#         # Convert the item to dict so we can give it an ID
#         full_item = dict(check_keywords(
#             item, name, item['pdf']
#         ))
#
#         full_item['id'] = scraped.id
#         database.update_full_publication(full_item)
#     else:
#         # File is already scraped in the database
#         os.unlink(item['pdf'])
