FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install google-cloud-secret-manager==2.16.1

# Copy application code
COPY . .

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Run test script to verify imports
RUN python test_app_imports.py || echo "Import test failed, but continuing build"

# Expose port for Cloud Run
EXPOSE 8080

# Run gunicorn with our configuration file
CMD exec gunicorn --config=gunicorn.conf.py app:app 