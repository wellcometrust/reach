FROM reach.base

WORKDIR /opt/reach

COPY ./requirements.txt /opt/reach/requirements.web.txt

RUN pip install -U pip && \
        python3 -m pip install -r /opt/reach/requirements.web.txt

COPY ./app /opt/reach/web
COPY ./build /opt/reach/build
