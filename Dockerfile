FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install additional dependencies needed by the application
RUN pip install --no-cache-dir flask sqlalchemy boto3 requests authlib python-pptx

# Copy the flask app
COPY flask_app/ ./flask_app/

# Set environment variables
ENV PYTHONPATH=/app
ENV FLASK_APP=flask_app/app.py
ENV FLASK_ENV=production

# Expose port
EXPOSE 5000

# Command to run the application
CMD ["flask", "run", "--host=0.0.0.0"]
