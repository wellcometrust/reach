# Use a basic Python image
FROM python:3.6.4

WORKDIR /reference_parser


COPY ./utils/* /reference_parser/utils/
COPY ./main.py /reference_parser/main.py
COPY ./models.py /reference_parser/models.py
COPY ./settings.py /reference_parser/settings.py

COPY ./Pipfile /reference_parser/Pipfile
COPY ./Pipfile.lock /reference_parser/Pipfile.lock

# Install dependencies using pipenv
RUN pip install -U -q pip
RUN pip install pipenv
RUN pipenv install --system --deploy

CMD ["python", "main.py"]
