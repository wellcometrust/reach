FROM reach.base

WORKDIR /opt/reach

COPY ./requirements.txt /opt/reach/requirements.evaluator.txt

RUN pip install -U pip && \
        python3 -m pip install -r /opt/reach/requirements.evaluator.txt


COPY ./evaluator_task.py /opt/reach/evaluator_task.py

# Give execution rights to the entrypoint Python script
RUN chmod +x /opt/reach/evaluator_task.py

ENTRYPOINT ["/opt/reach/evaluator_task.py"]
