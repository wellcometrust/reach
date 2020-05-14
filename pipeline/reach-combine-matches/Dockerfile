FROM reach.base

WORKDIR /opt/reach

COPY ./requirements.txt /opt/reach/requirements.combinefuzzymatches.txt

RUN pip install -U pip && \
        python3 -m pip install -r /opt/reach/requirements.combinefuzzymatches.txt


COPY ./combine_matches_task.py /opt/reach/combine_matches_task.py

# Give execution rights to the entrypoint Python script
RUN chmod +x /opt/reach/combine_matches_task.py

ENTRYPOINT ["/opt/reach/combine_matches_task.py"]
