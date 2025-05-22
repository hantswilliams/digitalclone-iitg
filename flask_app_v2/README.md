# DigitalClone IITG - Flask App V2

A modular Flask application for generating digital avatars with voice cloning capabilities.

## About

This is the v2 implementation of the DigitalClone IITG Flask application, built following the "LEGO Approach" described in our manuscript. The application is designed with modular components that can be swapped out or upgraded independently.

## Features

- Audio generation using PlayHT and other providers
- Video generation using SadTalker
- Presentation creation and SCORM packaging
- Project management for organizing media
- Asynchronous processing with Celery
- RESTful API design
- OAuth authentication

## Project Structure

```
flask_app_v2/
├── app/
│   ├── __init__.py                 # App factory pattern
│   ├── config.py                   # Configuration management
│   ├── extensions.py               # Flask extensions (SQLAlchemy, Celery)
│   ├── api/                        # API endpoints
│   ├── auth/                       # Authentication module
│   ├── models/                     # Database models
│   ├── services/                   # Business logic services
│   ├── tasks/                      # Celery background tasks
│   ├── templates/                  # Jinja templates
│   ├── static/                     # Static assets
│   └── utils/                      # Utility functions
├── migrations/                     # Database migrations
├── tests/                          # Unit and integration tests
├── .env.example                    # Example environment variables
├── celery_worker.py                # Celery worker entry point
├── requirements.txt                # Project dependencies
└── run.py                          # Application entry point
```

## Installation

1. Clone the repository
2. Create a virtual environment and activate it:
   ```
   python3.11 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Create a `.env` file based on `.env.example` and fill in your API keys

## Running the Application

1. Start the Flask application:
   ```
   python run.py
   ```

2. Start the Celery worker in a separate terminal:
   ```
   celery -A celery_worker.celery worker --loglevel=info
   ```

3. Access the application at http://localhost:5000

## Development

1. Set the environment to development mode:
   ```
   export FLASK_ENV=development
   ```

2. Run tests:
   ```
   pytest
   ```

## Deployment

### Using Docker

This application can be run using Docker containers for easier deployment and development.

#### Prerequisites

- Docker
- Docker Compose

#### Docker Setup

1. Copy the environment template file:
   ```
   cp .env.example .env
   ```

2. Edit the `.env` file with your configuration

3. Use the included script to manage Docker containers:
   ```
   ./docker.sh dev     # Start development environment
   ./docker.sh prod    # Start production environment
   ./docker.sh stop    # Stop containers
   ./docker.sh help    # Show all available commands
   ```

4. Access the application at http://localhost:5000

#### Manual Docker Commands

If you prefer to use Docker Compose directly:

For development:
```
docker-compose up -d
```

For production:
```
docker-compose -f docker-compose.prod.yml up -d
```

### Cloud Deployment

See the `getting_started.md` and `cloud_deployment.md` files in the repository for detailed cloud deployment instructions.
