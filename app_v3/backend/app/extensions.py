"""
Flask extensions initialization
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from celery import Celery
import redis


# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

# Initialize Redis client for JWT blocklist
redis_client = None

# Initialize Celery
celery = Celery('voice_clone_tasks')


def make_celery(app):
    """Create Celery instance with Flask app context"""
    # Configure Celery with new-style settings
    celery.conf.update(
        broker_url=app.config.get('broker_url', app.config.get('CELERY_BROKER_URL')),
        result_backend=app.config.get('result_backend', app.config.get('CELERY_RESULT_BACKEND')),
        task_serializer=app.config.get('task_serializer', 'json'),
        result_serializer=app.config.get('result_serializer', 'json'),
        accept_content=app.config.get('accept_content', ['json']),
        timezone=app.config.get('timezone', 'UTC'),
        enable_utc=app.config.get('enable_utc', True),
    )
    
    # Store the Flask app instance
    celery.flask_app = app
    
    class ContextTask(celery.Task):
        """Make celery tasks work with Flask app context"""
        def __call__(self, *args, **kwargs):
            with app.app_context():
                try:
                    # Ensure we start with a fresh database session
                    db.session.remove()
                    return self.run(*args, **kwargs)
                finally:
                    # Clean up session after task completion
                    db.session.remove()
    
    celery.Task = ContextTask
    return celery


def init_redis(app):
    """Initialize Redis client"""
    global redis_client
    redis_url = app.config.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    
    try:
        redis_client = redis.from_url(redis_url)
        # Test the connection
        redis_client.ping()
        app.logger.info("Redis connected successfully")
    except Exception as e:
        app.logger.warning(f"Redis connection failed: {e}. Using in-memory fallback for JWT blocklist.")
        redis_client = None
