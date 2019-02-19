#!/bin/sh -e

psql <<EOF
CREATE DATABASE wsf_scraping;
CREATE DATABASE wsf_scraping_test;
EOF

psql wsf_scraping < /scraper.sql
psql wsf_scraping_test < /scraper.sql
