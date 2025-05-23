"""
Entry point for the Flask application
"""
import os
import sys
from app import create_app
from dotenv import load_dotenv

# Load environment variables from .env file or .env.dev in development
if os.path.exists('.env.dev'):
    load_dotenv('.env.dev')
else:
    load_dotenv()

# Default to development environment if not specified
config_name = os.getenv('FLASK_ENV', 'development')
print(f"Starting application with config: {config_name}")

try:
    # Create the Flask application
    app = create_app(config_name)
    print("Application created successfully")
    
    # Print connection info for debugging
    if config_name == 'development':
        db_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        # Mask password in output for security
        if 'postgres' in db_url:
            masked_url = db_url.replace('postgres:postgres', 'postgres:****')
            print(f"Database URL: {masked_url}")
        else:
            print(f"Database URL: {db_url}")
        print(f"Redis URL: {app.config.get('CELERY_BROKER_URL')}")
        print(f"Upload folder: {app.config.get('UPLOAD_FOLDER')}")
except Exception as e:
    print(f"Error creating application: {str(e)}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    raise

if __name__ == '__main__':
    # Run the application in debug mode for development
    debug_mode = os.getenv('FLASK_DEBUG', 'true').lower() in ('true', '1', 't')
    port = int(os.getenv('FLASK_PORT', '5002'))  # Use port 5002 by default, or from env var
    app.run(debug=debug_mode, host='0.0.0.0', port=port)
