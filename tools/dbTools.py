import psycopg2
import psycopg2.extras
import logging
from datetime import datetime


class DatabaseConnector:
    def __init__(self, host, user, password, dbname, port=5432):
        """Initialise an instance of the DatabaseConnector class and create:
         - self.logger: a logger to log errors
         - self.connection: the connection to the sqlite3 database
         - self.cursor: the cursor to execute requests on the database
        It also run the check_db method, creating the database if it doesn't
        exists yet.
        """

        self.logger = logging.getLogger(__name__)
        self.connection = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            port=port,
            dbname=dbname
        )
        self.cursor = self.connection.cursor(
            cursor_factory=psycopg2.extras.NamedTupleCursor
        )

    def __del__(self):
        """Commit all changes and close the database connection on the deletion
        of this instance from memory.
        """
        self.connection.commit()
        self.cursor.close()
        self.connection.close()

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

    def reset_scraped(self):
        """Set all the publications `scrape_again` attribute to 1, forcing the
        web scraper to download and analyse them again.
        """
        self._execute(
            "UPDATE publication SET scrape_again = %s",
            ('True',)
        )

    def clear_db(self):
        """Remove all the publications from the database."""
        self._execute(
            "DELETE FROM publication"
        )

    def get_scraping_info(self, file_hash):
        """Check if an publication had already been scraped by looking for its file
        hash into the database. If the publication exists, returns its id and
        its `scrape_again` value
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
        return result

    def get_publications(self, offset=0, limit=-1):
        """Return a list of publications. By default, returns every publications. This
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
        for publication in self.cursor.fetchall():
            result.append(publication)
        return result

    def insert_full_publication(self, publication, id_provider):
        """Insert an entire publication in the database and return its id."""
        self._execute(
            """
            INSERT INTO publication(title, url, pdf_name, file_hash,
                             authors, pub_year, pdf_text,
                             id_provider, datetime_creation)
            VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
            """,
            (publication['title'], publication['uri'], publication['pdf'],
             publication['hash'], publication.get('authors'),
             publication.get('year'), publication['text'], id_provider,
             datetime.now(),)
        )
        return self.cursor.fetchone().id

    def update_full_publication(self, publication):
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
            (publication['title'], publication['uri'], publication['pdf'],
             publication['hash'], publication.get('authors'),
             publication.get('year'), publication['text'], publication['id'],)
        )

    def insert_joints_and_text(self, table, items, id_publication):
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
                (id_publication, db_name_id, text_value,)
            )

    def insert_joints(self, table, items, id_publication):
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
                (id_publication, db_name_id,)
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

    def insert_publication(self, file_hash, url):
        """Try to insert an publication, composed by its file hash and url,
        into the database.
        """

        if len(url) >= 255:
            self.logger.warning(
                f'Article title ({url}) is too long ({len(url)}/255).'
            )
            url = url[:255]
        self._execute(
            "INSERT INTO publication (file_hash, url) VALUES (%s, %s)",
            (file_hash, url)
        )

    def get_finished_crawls(self):
        self._execute("SELECT * FROM spiders WHERE status = %s", ('finished',))
        result = []
        for publication in self.cursor:
            result.append(publication)
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
