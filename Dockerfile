# Use an official Python runtime as a parent image
FROM ubuntu:16.04

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
ADD . /app

RUN apt-get update -y
RUN apt-get upgrade -y

# Install Scrapy and Textract dependencies
RUN apt-get install -y python-dev \
    python3-dev \
    libxml2-dev \
    libxslt1-dev \
    antiword \
    unrtf \
    poppler-utils \
    pstotext \
    tesseract-ocr \
    flac \
    ffmpeg \
    lame \
    libmad0 \
    libsox-fmt-mp3 \
    sox \
    libjpeg-dev \
    swig \
    python-virtualenv \
    python-pip \
    idle-python2.7 \
    libgle3 \
    zlib1g-dev \
    libffi-dev \
    libssl-dev \
    libpulse-dev \
    build-essential \
    autoconf \
    libtool \
    pkg-config \
    python-opengl \
    python-imaging \
    python-pyrex

# Update pip
RUN pip install --upgrade pip
# Install any needed packages specified in requirements.txt
RUN pip install scrapy textract pybloom botocore

# Define environment variable
ENV NAME Scrapy
# Set proxy server, replace host:port with values for your servers
ENV http_proxy ""
ENV https_proxy ""

# Set proxy server, replace host:port with values for your servers
ENV HTTP_PROXY ""
ENV HTTPS_PROXY ""
# Run app.py when the container launches
CMD ["scrapy", "crawl", "who_iris"]
