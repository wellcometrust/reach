#!/bin/sh
#
# Updates files in static/vendor from the internet.

DESTDIR=$1
if [ -z "$DESTDIR" ]; then
    echo "Usage: $0 /path/to/static/vendor" >&2
    exit 1
fi


SPECTRE_VERSION=0.5.8


# Spectre CSS
mkdir -p $DESTDIR/spectre-${SPECTRE_VERSION}
curl -L https://github.com/picturepan2/spectre/archive/v${SPECTRE_VERSION}.tar.gz \
    | tar -C $DESTDIR/spectre-${SPECTRE_VERSION} \
        -xzf - \
        --strip-components 2 \
        spectre-${SPECTRE_VERSION}/dist
