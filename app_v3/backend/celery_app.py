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
from app.tasks.voice_tasks import echo_task, clone_voice_task, validate_voice_sample
from app.tasks.tts_tasks import text_to_speech_task, convert_audio_format
from app.tasks.video_tasks import generate_talking_head_video, generate_video_thumbnail, full_generation_pipeline
from app.tasks.export_tasks import export_video_format, create_html5_package, create_scorm_package

if __name__ == '__main__':
    celery.start()
