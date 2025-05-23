"""
Entry point for the Flask application
"""
import os
import sys
from app import create_app
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Default to development environment if not specified
config_name = os.getenv('FLASK_ENV', 'development')
print(f"Starting application with config: {config_name}")

try:
    # Create the Flask application
    app = create_app(config_name)
    print("Application created successfully")
except Exception as e:
    print(f"Error creating application: {str(e)}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    raise

if __name__ == '__main__':
    # Run the application in debug mode for development
    app.run(debug=config_name == 'development', host='0.0.0.0')
