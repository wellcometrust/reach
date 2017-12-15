# Use an official Python runtime as a parent image
FROM ubuntu:16.04

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
ADD . /app

RUN apt-get update -y
RUN apt-get upgrade -y

# Install Scrapy and Textract dependencies
RUN apt-get install -y python3 \
    python3-dev \
    gcc \
    python3-pip \

# Update pip
RUN pip3 install --upgrade pip
# Install any needed packages specified in requirements.txt
RUN pip3 install scrapy pdfminer.six botocore pybloom_live

# Define environment variable
ENV NAME Scrapy

# Run app.py when the container launches
CMD ["scrapy", "crawl", "who_iris"]
