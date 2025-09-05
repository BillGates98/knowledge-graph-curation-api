FROM --platform=linux/amd64 python:3.11-slim as build

ARG DATABASE_HOST
ARG DATABASE_USER
ARG DATABASE_PASSWORD
ARG DATABASE_NAME

ENV DATABASE_HOST=$DATABASE_HOST
ENV DATABASE_USER=$DATABASE_USER
ENV DATABASE_PASSWORD=$DATABASE_PASSWORD
ENV DATABASE_NAME=$DATABASE_NAME

RUN apt-get update -y
RUN apt-get install pkg-config -y
RUN apt-get install -y python3-dev build-essential
RUN apt-get install -y default-libmysqlclient-dev

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
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]