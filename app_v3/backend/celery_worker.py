"""
Celery worker entry point for the Voice-Cloned Talking-Head Lecturer backend
"""
import os
from app import create_app
from app.extensions import make_celery
from app.config import config

# Get configuration from environment
config_name = os.environ.get('FLASK_ENV', 'development')
app = create_app(config[config_name])

# Create Celery instance
celery = make_celery(app)

# Import tasks to register them with Celery
from app.tasks import voice_tasks, tts_tasks, video_tasks, export_tasks

if __name__ == '__main__':
    # Start Celery worker
    celery.start()
