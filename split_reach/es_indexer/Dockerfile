FROM reach.base

WORKDIR /opt/reach

COPY ./requirements.txt /opt/reach/requirements.indexer.txt

RUN pip install -U pip && \
        python3 -m pip install -r /opt/reach/requirements.indexer.txt


COPY ./index_task.py /opt/reach/index_task.py

# Give execution rights to the entrypoint Python script
RUN chmod +x /opt/reach/index_task.py

ENTRYPOINT ["/opt/reach/index_task.py"]
