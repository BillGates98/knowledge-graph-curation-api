# Pull base image
FROM ubuntu:22.04

# Set environment variables
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install Python3, pip3, and other utilities
RUN apt-get update && \
    apt-get --no-install-recommends install -y python3 python3-pip curl && \
    apt-get -y autoremove && \
    apt-get clean

# Upgrade pip
RUN pip3 install --upgrade pip

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the Django app to the container
COPY . /app/

# Create a new user 'django'
RUN useradd --create-home django
RUN chown -R django:django /app

# Copy the start-server.sh script to the container
COPY start-server.sh /app/start-server.sh

RUN chmod +x /app/start-server.sh
# Open the required port
EXPOSE 8000
# Switch to the new user 'django'
USER django
#Start the server
CMD ["/app/start-server.sh"]