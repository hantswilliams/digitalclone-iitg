"""
Celery worker entry point
"""
import os
from dotenv import load_dotenv
from app import create_app, celery
from app.config import config_by_name
from flask import Flask
from app.extensions import db

# Load environment variables - try .env.dev first for local development
if os.path.exists('.env.dev'):
    load_dotenv('.env.dev')
else:
    load_dotenv()

# Use a minimal app configuration for the Celery worker to avoid route conflicts
def create_celery_app():
    app = Flask(__name__)
    
    # Configure app with development settings
    config_name = os.getenv('FLASK_ENV', 'development')
    app.config.from_object(config_by_name[config_name])
    
    # Initialize only the required extensions
    db.init_app(app)
    
    # Initialize Celery with Redis URL from environment
    redis_url = os.getenv('REDIS_URL', 'redis://redis:6379/0')
    print(f"Celery worker using Redis URL: {redis_url}")
    celery.conf.update(broker_url=redis_url)
    celery.conf.update(result_backend=redis_url)
    
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    
    # Initialize database
    with app.app_context():
        try:
            db.create_all()
            print("Celery worker database tables created successfully")
        except Exception as e:
            print(f"Database initialization error in celery worker: {str(e)}")
    
    return app

# Create a minimal Flask app instance for Celery
app = create_celery_app()

# Import tasks to ensure they're registered with Celery
from app.tasks import audio_tasks, video_tasks, presentation_tasks
