import psycopg2
import psycopg2.extras
import logging
import os
from datetime import datetime


class DatabaseConnector:
    def __init__(self, database_url=None):
        """Initialise an instance of the DatabaseConnector class and create:
         - self.logger: a logger to log errors
         - self.connection: the connection to the sqlite3 database
         - self.cursor: the cursor to execute requests on the database
        It also run the check_db method, creating the database if it doesn't
        exists yet.
        """

        self.logger = logging.getLogger(__name__)
        if not database_url:
            database_url = os.getenv('DATABASE_URL')
        self.connection = psycopg2.connect(database_url)
        self.cursor = self.connection.cursor(
            cursor_factory=psycopg2.extras.NamedTupleCursor
        )
        self._check_db()

    def __del__(self):
        """Commit all changes and close the database connection on the deletion
        of this instance from memory.
        """
        self._close_all_spiders()
        self.connection.commit()
        self.cursor.close()
        self.connection.close()

    def _close_all_spiders(self):
        self._execute(
            """
            UPDATE spiders
            SET status = %s, end_time = CURRENT_TIMESTAMP;
            """,
            ('finished',)
        )

    def _execute(self, query, params=()):
        """Try to execute the SQL query passed by the query parameter, with the
        arguments passed by the tuple argument params.
        """
        try:
            self.cursor.execute(query, params)
            self.connection.commit()
        except psycopg2.Error as e:
            self.logger.error(
                'An exception had been encountered when executing %s',
                query,
            )
            raise

    def _check_db(self):
        """Create the tables needed by the web scraper if they don't exists."""
        self._execute(
            """
            CREATE TABLE IF NOT EXISTS article
            (
                id SERIAL PRIMARY KEY,
                url VARCHAR(255),
                file_hash VARCHAR(32),
                scrap_again BOOLEAN DEFAULT FALSE,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        self._execute(
            """
            CREATE TABLE IF NOT EXISTS spiders
            (
                id SERIAL PRIMARY KEY,
                name VARCHAR(64),
                uuid VARCHAR(64),
                status VARCHAR(255),
                end_time TIMESTAMP,
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        self.connection.commit()

    def reset_scraped(self):
        """Set all the articles `scrap_again` attribute to 1, forcing the web
        scraper to download and analyse them again.
        """
        self._execute(
            "UPDATE article SET scrap_again = %s",
            ('True',)
        )

    def clear_db(self):
        """Remove all the articles from the database."""
        self._execute(
            "DELETE FROM article"
        )

    def is_scraped(self, file_hash):
        """Check if an article had already been scraped by looking for its file
        hash into the database. If the article exists, returns its id and its
        `scrape_again` value
        """
        self._execute(
            """
            SELECT id, scrape_again
            FROM publication
            WHERE file_hash = %s;
            """,
            (file_hash,)
        )
        result = self.cursor.fetchone()
        if result:
            return result.id, result.scrape_again
        else:
            return (None, None)

    def get_articles(self, offset=0, limit=-1):
        """Return a list of articles. By default, returns every articles. This
        method accepts start and end arguments to paginate results.
        """
        if limit > 0:
            self._execute(
                """
                    SELECT title, file_hash, url
                    FROM publication LIMIT %s OFFSET %s
                """,
                (offset, limit,)
            )
        else:
            self._execute("SELECT title, file_hash, url FROM publication")
        result = []
        for article in self.cursor.fetchall():
            result.append(article)
        return result

    def insert_full_article(self, article, id_provider):
        """Insert an entire article in the database and return its id."""
        self._execute(
            """
            INSERT INTO publication(title, url, pdf_name, file_hash,
                             authors, pub_year, pdf_text,
                             id_provider, datetime_creation)
            VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
            """,
            (article['title'], article['uri'], article['pdf'],
             article['hash'], article.get('authors', ''), article['year'],
             article['text'], id_provider, datetime.now(),)
        )
        return self.cursor.fetchone().id

    def update_full_article(self, article):
        self._execute(
            """
            UPDATE publication
            SET
                title=%s,
                url=%s,
                pdf_name=%s,
                file_hash=%s,
                authors=%s,
                pub_year=%s,
                pdf_text=%s,
            WHERE id=%s;
            """,
            (article['title'], article['uri'], article['pdf'],
             article['hash'], article.get('authors', ''), article['year'],
             article['text'], article['id'],)
        )

    def insert_joints_and_text(self, table, items, id_article):
        """Create both a name table and a joint table between a publication and
        another item with a 0-n or 1-n cardinality, containing a text element.
        """
        if not items:
            return
        for name, text_value in items.items():
            db_name_id = self.get_or_create_name(name, table)
            self._execute(
                """
                    INSERT
                    INTO publications_{table}s(
                        id_publication,
                        id_{table},
                        text_content
                    )
                    VALUES(%s, %s, %s);
                """.format(table=table),
                (id_article, db_name_id, text_value,)
            )

    def insert_joints(self, table, items, id_article):
        """Create both a name table and a joint table between a publication and
        another item with a 0-n or 1-n cardinality.
        """
        if not items:
            return
        for name in items:
            db_name_id = self.get_or_create_name(name, table)
            self._execute(
                """
                    INSERT
                    INTO publications_{table}s(
                        id_publication,
                        id_{table}
                    )
                    VALUES(%s, %s);
                """.format(table=table),
                (id_article, db_name_id,)
            )

    def get_or_create_name(self, name, table):
        """Insert a `name` like element in a table if it doesn't exists and
        returns its ID. If it already exists, just returns the ID.
        """
        self._execute(
            'SELECT id FROM {table} WHERE name = %s'.format(table=table),
            (name,)
        )
        item = self.cursor.fetchone()
        if item:
            return item.id
        else:
            self._execute(
                """
                INSERT INTO {table}(name)
                VALUES(%s)
                RETURNING id;
                """.format(table=table),
                (name,)
            )
            return self.cursor.fetchone().id

    def insert_article(self, file_hash, url):
        """Try to insert an article, composed by its file hash and url,
        into the database.
        """

        if len(url) >= 255:
            self.logger.warning(
                f'Article title ({url}) is too long ({len(url)}/255).'
            )
            url = url[:255]
        self._execute(
            "INSERT INTO article (file_hash, url) VALUES (%s, %s)",
            (file_hash, url)
        )

    def get_finished_crawls(self):
        self._execute("SELECT * FROM spiders WHERE status = %s", ('finished',))
        result = []
        for article in self.cursor:
            result.append(article)
        return result

    def insert_spider(self, name, uuid):
        self._execute(
            "INSERT INTO spiders (name, uuid, status) VALUES (%s, %s, %s)",
            (name[:255], uuid, 'running')
        )

    def close_spider(self, uuid):
        self._execute(
            """
            UPDATE spiders
            WHERE uuid = %s
            SET status = %s, end_time = CURRENT_TIMESTAMP;
            """,
            (uuid, 'finished')
        )
