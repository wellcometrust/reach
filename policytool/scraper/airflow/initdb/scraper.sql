CREATE DATABASE airflow;
CREATE DATABASE airflow_celery_results;

CREATE DATABASE wsf_scraping;
CREATE DATABASE wsf_scraping_test;

CREATE TABLE IF NOT EXISTS section
(
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    datetime_creation TIMESTAMP,
    datetime_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS keyword
(
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    datetime_creation TIMESTAMP,
    datetime_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS provider
(
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    datetime_creation TIMESTAMP,
    datetime_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS type
(
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    datetime_creation TIMESTAMP,
    datetime_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS subject
(
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    datetime_creation TIMESTAMP,
    datetime_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS publication
(
    id SERIAL PRIMARY KEY,
    title VARCHAR(1024),
    url TEXT,
    pdf_name VARCHAR(1024),
    file_hash VARCHAR(32),
    authors VARCHAR(1024),
    pub_year  VARCHAR(4),
    pdf_text TEXT,
    scrape_again BOOLEAN,
    id_provider INT REFERENCES "provider",
    datetime_creation TIMESTAMP,
    datetime_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS publications_sections
(
    id_publication INT REFERENCES "publication",
    id_section INT REFERENCES "section",
    text_content TEXT,
    PRIMARY KEY(id_publication, id_section)
);

CREATE TABLE IF NOT EXISTS publications_keywords
(
    id_publication INT REFERENCES "publication",
    id_keyword INT REFERENCES "keyword",
    text_content TEXT,
    PRIMARY KEY(id_publication, id_keyword)
);

CREATE TABLE IF NOT EXISTS publications_types
(
    id_publication INT REFERENCES "publication",
    id_type INT REFERENCES "type",
    PRIMARY KEY(id_publication, id_type)
);

CREATE TABLE IF NOT EXISTS publications_subjects
(
    id_publication INT REFERENCES "publication",
    id_subject INT REFERENCES "subject",
    PRIMARY KEY(id_publication, id_subject)
);
