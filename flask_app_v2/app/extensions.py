"""
Flask extensions initialization
"""
import os
from flask_sqlalchemy import SQLAlchemy
from celery import Celery
from authlib.integrations.flask_client import OAuth
from flask_bcrypt import Bcrypt

# Initialize extensions here to avoid circular imports
db = SQLAlchemy()
celery = Celery(__name__, broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
oauth = OAuth()
bcrypt = Bcrypt()
