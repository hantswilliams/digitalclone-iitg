"""
Entry point for the Flask application
"""
import os
from app import create_app
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Default to development environment if not specified
config_name = os.getenv('FLASK_ENV', 'development')

# Create the Flask application
app = create_app(config_name)

if __name__ == '__main__':
    # Run the application in debug mode for development
    app.run(debug=config_name == 'development', host='0.0.0.0')
