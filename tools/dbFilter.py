import sqlite3


def is_scraped(url):
    #  Init sqlite db to filter PDFs
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

    cursor.execute(
        "SELECT * FROM article WHERE url LIKE ? AND scrap_again=0",
        ('%' + url,)
    )
    result = cursor.fetchone()
    if result:
        connection.close()
        return True
    else:
        connection.close()
        return False


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
