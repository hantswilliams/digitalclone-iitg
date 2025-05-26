"""
Celery tasks package
"""
from .celery_app import celery
from .voice_tasks import clone_voice_task, validate_voice_sample, echo_task
from .tts_tasks import text_to_speech_task, convert_audio_format, generate_speech, validate_tts_service
from .video_tasks import generate_talking_head_video, generate_video_thumbnail, full_generation_pipeline
from .export_tasks import export_video_format, create_scorm_package, create_html5_package

__all__ = [
    'celery',
    'echo_task',
    'clone_voice_task',
    'validate_voice_sample',
    'text_to_speech_task',
    'convert_audio_format',
    'generate_speech',
    'validate_tts_service',
    'generate_talking_head_video',
    'generate_video_thumbnail',
    'full_generation_pipeline',
    'export_video_format',
    'create_scorm_package',
    'create_html5_package'
]
