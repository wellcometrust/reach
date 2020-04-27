
CREATE DATABASE reach;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS epmc_metadata (
    uuid UUID PRIMARY KEY NOT NULL DEFAULT uuid_generate_v4(),
    id TEXT NULL,
    source TEXT NULL,
    pmid TEXT NULL,
    pmcid TEXT NULL,
    doi TEXT NULL,
    title TEXT NULL,
    authors JSONB NOT NULL DEFAULT '{}',
    journal_title TEXT NULL,
    journal_issue TEXT NULL,
    journal_volume TEXT NULL,
    pub_year INT NULL,
    journal_issn TEXT NULL,
    page_info TEXT NULL,
    pub_type TEXT NULL,
    created TIMESTAMPTZ NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    modified TIMESTAMPTZ NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc')
);

CREATE TABLE IF NOT EXISTS reach_citations (
    uuid UUID PRIMARY KEY NOT NULL DEFAULT uuid_generate_V4(),
    epmc_id UUID REFERENCES epmc_metadata (uuid) NOT NULL,
    policies UUID[] NOT NULL DEFAULT '{}',
    created TIMESTAMPTZ NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    modified TIMESTAMPTZ NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc')
);

CREATE TABLE IF NOT EXISTS reach_policies (
    uuid UUID PRIMARY KEY NOT NULL DEFAULT uuid_generate_V4(),
    title TEXT NULL,
    url TEXT NULL,
    fulltext TEXT NULL,
    created TIMESTAMPTZ NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    modified TIMESTAMPTZ NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc')
);
