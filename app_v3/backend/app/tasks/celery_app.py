"""
Celery configuration and initialization
"""
from celery import Celery

def create_celery(app=None):
    """Create and configure Celery instance"""
    celery = Celery(
        app.import_name if app else 'voice_clone_tasks',
        broker=app.config['CELERY_BROKER_URL'] if app else 'redis://localhost:6379/0',
        backend=app.config['CELERY_RESULT_BACKEND'] if app else 'redis://localhost:6379/0'
    )
    
    if app:
        celery.conf.update(app.config)
        
        class ContextTask(celery.Task):
            """Make celery tasks work with Flask app context"""
            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return self.run(*args, **kwargs)
        
        celery.Task = ContextTask
    
    return celery

# Default Celery instance for development
celery = create_celery()
