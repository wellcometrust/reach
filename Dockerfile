# Use a basic Python image
FROM python:3.6.4

WORKDIR /reference_parser


COPY ./dynamodb.py /reference_parser/dynamodb.py
COPY ./s3.py /reference_parser/s3.py
COPY ./main.py /reference_parser/main.py
COPY ./models.py /reference_parser/models.py
COPY ./separate.py /reference_parser/separate.py
COPY ./predict.py /reference_parser/predict.py
COPY ./fuzzymatch.py /reference_parser/fuzzymatch.py
COPY ./requirements.txt /reference_parser/requirements.txt
COPY ./settings.py /reference_parser/settings.py

RUN pip install -r requirements.txt

CMD ["python", "main.py"]
