FROM reach.base

WORKDIR /opt/reach

COPY ./requirements.txt /opt/reach/requirements.parser.txt

RUN pip install -U pip && \
        python3 -m pip install -r /opt/reach/requirements.parser.txt


COPY ./parser_task.py /opt/reach/parser_task.py
COPY ./pdf_parser /opt/reach/pdf_parser
COPY ./normalizer /opt/reach/normalizer

# Give execution rights to the entrypoint Python script
RUN chmod +x /opt/reach/parser_task.py

ENTRYPOINT ["/opt/reach/parser_task.py"]
