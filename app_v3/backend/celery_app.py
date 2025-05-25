"""
Celery worker entry point
"""
import os
from app import create_app
from app.extensions import make_celery

# Create Flask app
flask_app = create_app()

# Create Celery instance
celery = make_celery(flask_app)

# Import tasks to register them with Celery
from app.tasks import echo_task, clone_voice_task, text_to_speech_task, generate_talking_head_video

if __name__ == '__main__':
    celery.start()
