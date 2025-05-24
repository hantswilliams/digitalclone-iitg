"""
flask_app_v2 - A modular Flask application for Digital Clone project
Using the "LEGO Approach" for swappable components
"""
from flask import Flask
from flask_login import LoginManager
from app.extensions import db, celery, oauth
from app.config import config_by_name
import logging
import os
import datetime


def create_app(config_name='default'):
    app = Flask(__name__)
    
    # Configure app
    app.config.from_object(config_by_name[config_name])
    
    # Initialize extensions
    db.init_app(app)
    init_celery(app)
    init_oauth(app)
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.models import User
        return User.query.filter_by(user_id=user_id).first()
    
    # Initialize database and create tables
    init_db(app)
    
    # Set up logging
    if not app.debug:
        # Configure production logging
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        app.logger.addHandler(handler)
        app.logger.setLevel(logging.INFO)
    
    # Register blueprints
    from app.api.routes import api_bp
    from app.auth.routes import auth_bp
    from app.errors import errors_bp
    from app.views import views_bp
    
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(errors_bp)
    app.register_blueprint(views_bp)
    
    # Set up advanced logging with the util logger
    from app.utils.logger import configure_logger
    configure_logger(app)
    
    # Add template context processors
    @app.context_processor
    def inject_now():
        return {'now': datetime.datetime.now()}
    
    # Initialize request tracking middleware
    from app.utils.middleware import init_request_middleware
    init_request_middleware(app)
    
    return app


def init_celery(app=None):
    """Initialize Celery with app context"""
    celery.conf.update(broker_url=app.config['CELERY_BROKER_URL'])
    celery.conf.update(result_backend=app.config['CELERY_RESULT_BACKEND'])
    
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery


def init_oauth(app):
    """Initialize OAuth with app"""
    oauth.init_app(app)
    
    # Configure OAuth providers (Google)
    if app.config.get('GOOGLE_CLIENT_ID') and app.config.get('GOOGLE_CLIENT_SECRET'):
        oauth.register(
            name='google',
            client_id=app.config['GOOGLE_CLIENT_ID'],
            client_secret=app.config['GOOGLE_CLIENT_SECRET'],
            server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
            client_kwargs={
                'scope': 'openid email profile'
            }
        )


def init_db(app):
    """Initialize database with automatic table creation and schema updates"""
    from app.models.models import User
    
    with app.app_context():
        try:
            # First, try to create all tables (for new installations)
            db.create_all()
            app.logger.info("Database tables created/verified successfully")
            
            # Check and add missing columns to existing tables
            _add_missing_columns(app)
            
            # Check if we need to seed initial data
            if not User.query.first():
                app.logger.info("No users found. Creating initial admin user...")
                admin = User(
                    user_id="admin",
                    username="admin",
                    email="admin@example.com",
                    name="Admin User",
                    permissions="admin"
                )
                # Set password if using basic auth
                from werkzeug.security import generate_password_hash
                admin.password = generate_password_hash("admin")  # Change this in production!
                
                db.session.add(admin)
                db.session.commit()
                app.logger.info("Initial admin user created successfully")
        except Exception as e:
            app.logger.error(f"Database initialization error: {str(e)}")
            raise e


def _add_missing_columns(app):
    """Add missing columns to existing tables"""
    from sqlalchemy import text
    
    try:
        # Check if cloned_voice_id column exists in audio table
        result = db.session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='audio' AND column_name='cloned_voice_id'
        """))
        
        if not result.fetchone():
            app.logger.info("Adding missing cloned_voice_id column to audio table...")
            db.session.execute(text("""
                ALTER TABLE audio 
                ADD COLUMN cloned_voice_id INTEGER REFERENCES cloned_voice(id)
            """))
            db.session.commit()
            app.logger.info("Successfully added cloned_voice_id column")
            
        # Check if cloned_voice table exists, if not create it
        result = db.session.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name='cloned_voice'
        """))
        
        if not result.fetchone():
            app.logger.info("Creating cloned_voice table...")
            db.session.execute(text("""
                CREATE TABLE cloned_voice (
                    id SERIAL PRIMARY KEY,
                    voice_name VARCHAR(255) NOT NULL,
                    voice_id VARCHAR(255) NOT NULL,
                    provider VARCHAR(50) NOT NULL,
                    voice_type VARCHAR(50) DEFAULT 'cloned',
                    status VARCHAR(50) DEFAULT 'processing',
                    sample_url VARCHAR(500),
                    user_id VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """))
            db.session.commit()
            app.logger.info("Successfully created cloned_voice table")
            
    except Exception as e:
        app.logger.warning(f"Could not check/add missing columns (probably SQLite): {str(e)}")
        # If we're using SQLite, just recreate all tables
        if 'sqlite' in str(db.engine.url):
            app.logger.info("Using SQLite - recreating tables to ensure schema is up to date")
            db.drop_all()
            db.create_all()
            app.logger.info("SQLite tables recreated successfully")
