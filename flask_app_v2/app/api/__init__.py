"""
API Blueprint initialization
"""
from flask import Blueprint

api_bp = Blueprint('api', __name__)

# Import routes after creating Blueprint to avoid circular imports
from app.api import routes
