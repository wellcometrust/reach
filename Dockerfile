# Use an official Python runtime as a parent image
FROM ubuntu:16.04

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
ADD . /app

RUN apt-get update -qq
RUN apt-get upgrade -qqy

# Install Scrapy and Textract dependencies
RUN apt-get install -qqqy \
    python3 \
    python3-dev \
    gcc \
    python3-pip

# Update pip
RUN pip3 install -qqq --upgrade pip
# Install any needed packages specified in requirements.txt
RUN pip3 install -qqq -r requirements.txt

# Run app.py when the container launches
CMD ["scrapy", "crawl", "who_iris"]
