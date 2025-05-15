FROM python:3.9-slim

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

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV LOG_LEVEL=INFO
ENV LOG_TO_STDOUT=True
ENV PREFERRED_URL_SCHEME=https

# Expose port for Cloud Run
EXPOSE 8080

# Copy database configuration update script
COPY deploy/scripts/update_db_config.py /app/update_db_config.py
RUN chmod +x /app/update_db_config.py

# Create startup script
RUN echo '#!/bin/bash\n\
echo "Starting Mobilize CRM application..."\n\
echo "Python version: $(python --version)"\n\
echo "Current directory: $(pwd)"\n\
echo "Running database configuration update script..."\n\
python /app/update_db_config.py\n\
echo "Starting application with gunicorn..."\n\
exec gunicorn --bind :8080 --workers 3 --threads 8 --timeout 300 --access-logfile - --error-logfile - wsgi:app\n' > /app/startup.sh \
    && chmod +x /app/startup.sh

# Start the application
CMD ["/app/startup.sh"]
