#!/bin/sh -e
# Wrapper for running commands inside the web build image.
# Mirrors what's in ../docker-compose.yml.

DIR=$(cd $(dirname $0)/..; pwd)
BUILD_DIR=$(cd $(dirname $0)/../../../build/web/static; pwd)

# NODE_ENV=production silences an erroneous warning about postcss
# not being configured that I couldn't silence otherwise. :-(
docker run \
    --rm \
    -e NODE_ENV=production \
    -v $BUILD_DIR/:/build/web/static \
    -v $DIR/gulpfile.js:/src/gulpfile.js \
    -v $DIR/static:/src/static \
    reach-web-build:latest \
    $*
