import unittest
import os
from tools import DatabaseConnector


class TestDBTools(unittest.TestCase):

    def setUp(self):
        self.database = DatabaseConnector(os.getenv('DATABASE_URL_TEST'))

    def test_queries(self):
        self.database.insert_article(
            '0' * 32,
            'http://example.com/pdf.pdf'
        )
        self.assertTrue(self.database.is_scraped('0' * 32))
        self.database._execute(
            'UPDATE article SET scrap_again = TRUE WHERE file_hash = %s',
            ('0' * 32,)
        )
        self.assertFalse(self.database.is_scraped('0' * 32))
        self.database._execute(
            'DELETE FROM article WHERE file_hash = %s',
            ('0' * 32,)
        )
        self.assertFalse(self.database.is_scraped('0' * 32))
