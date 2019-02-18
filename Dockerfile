# Use a basic Python image
FROM python:3.6.4-slim-stretch

WORKDIR /reference_parser

COPY utils /reference_parser/utils
COPY tests /reference_parser/tests
COPY reference_parser_models /reference_parser/reference_parser_models

COPY refparse.py /reference_parser/refparse.py
COPY models.py /reference_parser/models.py
COPY settings.py /reference_parser/settings.py

COPY requirements.txt /reference_parser/requirements.txt

RUN pip install -U pip
RUN pip install -r requirements.txt

CMD ["python", "refparse.py"]
