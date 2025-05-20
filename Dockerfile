FROM python:3.9-slim
# Build version 3.0 - Force rebuild with CSRF token field implementation
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    postgresql-client \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies with explicit psycopg2-binary
RUN pip install --no-cache-dir psycopg2-binary
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1
ENV FIREBASE_PROJECT_ID=mobilize-crm
ENV SKIP_DB_INIT=True
ENV LOG_LEVEL=INFO
ENV LOG_TO_STDOUT=True
ENV PYTHONDONTWRITEBYTECODE=1
ENV GOOGLE_CLOUD_PROJECT=mobilize-crm
ENV PREFERRED_URL_SCHEME=https
# Set a placeholder for Firebase credentials that will be replaced by the secret in Cloud Run
ENV FIREBASE_CREDENTIALS='{}'

# Create a test script to verify environment during build
RUN echo "#!/bin/bash\necho 'Firebase Project ID:' \$FIREBASE_PROJECT_ID\necho 'Flask App:' \$FLASK_APP\n" > /app/verify_env.sh \
    && chmod +x /app/verify_env.sh

# Run verification as part of the build process
RUN /app/verify_env.sh

# Make start script executable
RUN chmod +x start.sh

# Expose port for Cloud Run
EXPOSE 8080

# Create a simple health check endpoint
RUN echo "from flask import Flask\napp = Flask(__name__)\n@app.route('/health')\ndef health_check():\n    return {'status': 'ok'}\n\nif __name__ == '__main__':\n    app.run(host='0.0.0.0', port=8080)" > health_check.py

# Use our startup script
# Use optimized Gunicorn configuration for better performance
# Number of workers = (2 * CPU cores) + 1
# We're setting to 3 for a 1 CPU instance
CMD exec gunicorn --bind :8080 --workers 3 --threads 8 --timeout 0 --keep-alive 5 --max-requests 1000 --max-requests-jitter 50 wsgi:app