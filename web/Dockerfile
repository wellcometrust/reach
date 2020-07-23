FROM node:12.7.0-alpine as builder

WORKDIR /opt/reach/web

COPY ./package.json /opt/reach/web/package.json

RUN \
    npm install -g parcel && \
    npm install

COPY ./web/src /opt/reach/web/src

RUN parcel build /opt/reach/web/src/js/app.js --out-dir /opt/reach/web/static/js/
RUN parcel build /opt/reach/web/src/css/style.less --out-dir /opt/reach/web/static/css/


FROM reach.base

WORKDIR /opt/reach

COPY ./requirements.txt /opt/reach/requirements.web.txt

RUN pip install -U pip && \
        python3 -m pip install -r /opt/reach/requirements.web.txt

COPY ./web /opt/reach/web
COPY --from=builder /opt/reach/web/static /opt/reach/build

COPY ./web/src/images/ /opt/reach/web/build/static/images/
COPY ./web/src/favicon/ /opt/reach/web/build/static/favicon/
COPY ./web/src/favicon/favicon.ico /opt/reach/web/favicon.ico
