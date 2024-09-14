FROM python:3.11-slim
LABEL maintainer="Dawit"
ENV PYTHONUNBUFFERED 1

# Copy requirements and application code
COPY ./requirements.txt /tmp/requirements.txt
COPY ./app /app

# Set working directory
WORKDIR /app

# Expose port
EXPOSE 8003

# Install system dependencies and Python packages
RUN apt-get update && \
    apt-get install -y \
    libglib2.0-0 \
    libgl1-mesa-glx \
    postgresql-client \
    build-essential \
    libjpeg-dev \
    zlib1g-dev && \
    pip install --upgrade pip setuptools wheel cmake && \
    pip install -r /tmp/requirements.txt && \
    rm -rf /var/lib/apt/lists/* && \
    adduser --disabled-password --no-create-home django-user && \
    mkdir -p /vol/web/media && \
    mkdir -p /vol/web/static && \
    chown -R django-user:django-user /vol && \
    chmod -R 755 /vol

USER django-user
