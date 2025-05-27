#!/usr/bin/env python3
"""
Celery worker runner for the Voice Clone app with proper Flask context
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the backend directory to the path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app import create_app
from app.extensions import make_celery

if __name__ == '__main__':
    # Create Flask app and configure Celery with proper context
    app = create_app()
    
    # Initialize Celery with Flask app context
    celery = make_celery(app)
    
    # Import all tasks to register them
    from app.tasks import *
    
    # Start the worker using the worker method
    celery.worker_main(argv=['worker', '--loglevel=info'])
