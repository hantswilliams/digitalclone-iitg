"""
flask_app_v2 - A modular Flask application for Digital Clone project
Using the "LEGO Approach" for swappable components
"""
from flask import Flask
from flask_migrate import Migrate, upgrade
from flask_login import LoginManager
from app.extensions import db, celery, oauth
from app.config import config_by_name
import logging
import os
import datetime
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
    """Initialize database and migrations"""
    from flask_migrate import Migrate, upgrade
    from app.models.models import User

    migrate = Migrate(app, db)
    
    with app.app_context():
        try:
            # Try to upgrade the database
            upgrade()
            
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
            # If upgrade fails (no migrations yet), create all tables
            db.create_all()
            app.logger.info("Created database tables directly as no migrations exist yet")
