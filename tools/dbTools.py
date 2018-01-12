import sqlite3


def check_db():
    connection = sqlite3.connect('db.sqlite3')
    cursor = connection.cursor()

    # If articles table does not exist, create it
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS article
        (
            id INTEGER PRIMARY KEY,
            title VARCHAR(64),
            url VARCHAR(255),
            scrap_again INTEGER(1) DEFAULT(0),
            Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

    connection.commit()
    connection.close()


def is_scraped(url):
    #  Init sqlite db to filter PDFs
    connection = sqlite3.connect('db.sqlite3')
    cursor = connection.cursor()

    cursor.execute(
        "SELECT id FROM article WHERE url LIKE ? AND scrap_again=0",
        ('%' + url,)
    )
    result = cursor.fetchone()
    connection.close()
    return result if result else False


def insert_article(title, url):
    #  Init sqlite db to filter PDFs
    connection = sqlite3.connect('db.sqlite3')
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO article (title, url) VALUES (?, ?)",
        (title, url)
    )

    connection.commit()
    connection.close()


def reset_scraping_state():
    connection = sqlite3.connect('db.sqlite3')
    cursor = connection.cursor()
    cursor.execute(
        "DELERE FROM article"
    )

    connection.commit()
    connection.close()
