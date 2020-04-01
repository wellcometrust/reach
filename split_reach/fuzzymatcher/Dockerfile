FROM reach.base

WORKDIR /opt/reach

COPY ./requirements.txt /opt/reach/requirements.fuzzymatcher.txt

RUN pip install -U pip && \
        python3 -m pip install -r /opt/reach/requirements.fuzzymatcher.txt


COPY ./fuzzymatcher_task.py /opt/reach/fuzzymatcher_task.py

# Give execution rights to the entrypoint Python script
RUN chmod +x /opt/reach/fuzzymatcher_task.py

ENTRYPOINT ["/opt/reach/fuzzymatcher_task.py"]
