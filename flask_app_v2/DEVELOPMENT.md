# Development Setup Guide

This guide explains how to run the Flask application in development mode without Docker, while keeping the supporting services (Redis, PostgreSQL) containerized for convenience.

## Prerequisites

- Docker and Docker Compose installed
- Python 3.8+ installed
- pip package manager
- Virtual environment (recommended)

## Getting Started

1. **Set up your environment**

   It's recommended to use a virtual environment:

   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment variables**

   Copy the example development environment file:
   
   ```
   cp .env.dev.example .env.dev
   ```
   
   Edit `.env.dev` with your specific settings and API keys.

2. **Start the development environment**

   Run the development script which starts the necessary services and the Flask app:

   ```
   ./dev.sh
   ```

   This script will:
   - Start PostgreSQL and Redis in Docker containers
   - Start the Celery worker in a Docker container
   - Run database migrations if needed
   - Start the Flask application locally (outside Docker)

3. **Access the application**

   The application will be available at: http://localhost:5002

## Development Workflow

- Make changes to the Flask application code
- The server will automatically reload when you save changes (thanks to debug mode)
- No need to rebuild Docker containers for most code changes

## Environment Configuration

The `.env.dev` file contains the development environment configuration. Key settings:

- `DATABASE_URL`: Points to the PostgreSQL container (localhost:5433)
- `REDIS_URL`: Points to the Redis container (localhost:6380)
- `FLASK_DEBUG`: Set to true for automatic reloading

## Stopping the Environment

When you're done developing, stop the background services:

```
./stop_dev.sh
```

## Troubleshooting

### Database Connection Issues

If you have trouble connecting to the database, ensure:
- The PostgreSQL container is running: `docker ps | grep postgres`
- The port mapping is correct (5433:5432)
- Your DATABASE_URL is set correctly in .env.dev

### Redis/Celery Issues

If Celery tasks aren't running:
- Check that Redis is running: `docker ps | grep redis`
- Verify the REDIS_URL is correct in .env.dev
- Check Celery worker logs: `docker-compose -f docker-compose.dev.yml logs celery_worker`

## Running Tests

Tests can be run locally without Docker:

```
python -m pytest
```
