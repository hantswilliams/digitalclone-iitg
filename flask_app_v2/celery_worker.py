"""
Celery worker entry point
"""
from app import create_app, celery

# Create Flask app instance for Celery
app = create_app(config_name='development')

# Import tasks to ensure they're registered with Celery
from app.tasks import audio_tasks, video_tasks, presentation_tasks
