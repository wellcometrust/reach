#!/bin/sh
# Wrapper for running commands inside the web build image.
# Mirrors what's in ../docker-compose.yml.

DIR=$(cd $(dirname $0)/..; pwd)

mkdir -p $DIR/build/static

# NODE_ENV=production silences an erroneous warning about postcss
# not being configured that I couldn't silence otherwise. :-(
docker run \
    --rm \
    -e NODE_ENV=production \
    -v $DIR/build/static:/src/build/static \
    -v $DIR/gulpfile.js:/src/gulpfile.js \
    -v $DIR/static:/src/static \
    uk.ac.wellcome/policytool-web-build:latest \
    $*
