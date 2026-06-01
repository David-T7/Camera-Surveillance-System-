FROM python:3.11-slim-bookworm
ENV PYTHONUNBUFFERED 1

# 1. Install System Dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git pkg-config libglib2.0-0 libgl1-mesa-glx postgresql-client \
    build-essential libjpeg-dev zlib1g-dev cmake \
    libopenblas-dev liblapack-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. Upgrade pip and install build tools
RUN pip install --no-cache-dir --upgrade pip wheel && \
    pip install --no-cache-dir "setuptools==80.9.0"

# 3. Install requirements
COPY ./requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# 4. Install Face Recognition Models
RUN pip install --no-cache-dir git+https://github.com/ageitgey/face_recognition_models

# 5. Copy your application code
COPY ./app .

# 6. Setup User and Permissions
RUN adduser --disabled-password --no-create-home django-user && \
    mkdir -p /vol/web/media /vol/web/static && \
    chown -R django-user:django-user /vol /app && \
    chmod -R 755 /vol /app

USER django-user

# Expose port
EXPOSE 8003

# Default command
CMD ["python", "manage.py", "runserver", "0.0.0.0:8003"]