"""
Application entry point for the Voice-Cloned Talking-Head Lecturer backend
"""
import os
from app import create_app
from app.config import config

# Get configuration from environment
config_name = os.environ.get('FLASK_ENV', 'development')
app = create_app(config[config_name])

if __name__ == '__main__':
    # Development server
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=app.config.get('DEBUG', False)
    )
