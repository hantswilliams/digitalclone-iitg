"""
Flask application factory for Voice-Cloned Talking-Head Lecturer
"""
from flask import Flask, jsonify, request, make_response
from flask_cors import CORS

from .extensions import db, migrate, jwt, make_celery, init_redis
from .config import Config
from .auth import JWTBlocklist


def create_app(config_class=Config):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    init_redis(app)
    
    # Initialize storage service
    from .services.storage import storage_service
    storage_service.init_app(app)
    
    # Configure CORS - Allow all for development
    CORS(app, 
         origins=['http://localhost:3000', 'http://localhost:3001', 'http://localhost:3002'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
         allow_headers=['Content-Type', 'Authorization'],
         supports_credentials=True)
    
    # Initialize Celery with Flask app context
    celery = make_celery(app)
    
    # Configure JWT callbacks
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        """Check if JWT token is revoked"""
        jti = jwt_payload['jti']
        user_id = jwt_payload['sub']
        
        # Check if specific token is blocklisted
        if JWTBlocklist.is_token_revoked(jti):
            return True
            
        # Check if all user tokens are revoked
        return JWTBlocklist.is_user_tokens_revoked(user_id)
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        """Handle expired token"""
        return jsonify({
            'message': 'Token has expired',
            'success': False
        }), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        """Handle invalid token"""
        return jsonify({
            'message': 'Invalid token',
            'success': False
        }), 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        """Handle missing token"""
        return jsonify({
            'message': 'Authorization token is required',
            'success': False
        }), 401
    
    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        """Handle revoked token"""
        return jsonify({
            'message': 'Token has been revoked',
            'success': False
        }), 401
    
    # Register blueprints
    from .api import auth_bp, assets_bp, jobs_bp, generation_bp, export_bp, worker_bp, analytics_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(assets_bp, url_prefix='/api/assets')
    app.register_blueprint(jobs_bp, url_prefix='/api/jobs')
    app.register_blueprint(generation_bp, url_prefix='/api/generate')
    app.register_blueprint(export_bp, url_prefix='/api/export')
    app.register_blueprint(worker_bp, url_prefix='/api/worker')
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'service': 'voice-clone-api'}
    
    return app
