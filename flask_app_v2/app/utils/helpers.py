"""
Utility functions and helpers
"""
import logging
import os
import uuid
from flask import current_app


def setup_logger():
    """Set up application-wide logger"""
    logger = logging.getLogger('digitalclone')
    logger.setLevel(logging.INFO)
    
    # Create handlers
    c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler('app.log')
    c_handler.setLevel(logging.INFO)
    f_handler.setLevel(logging.INFO)
    
    # Create formatters and add to handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    c_handler.setFormatter(formatter)
    f_handler.setFormatter(formatter)
    
    # Add handlers to the logger
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)
    
    return logger


def generate_unique_filename(filename):
    """Generate a unique filename with UUID to avoid collisions"""
    # Get file extension
    _, file_extension = os.path.splitext(filename)
    # Generate a unique filename
    unique_filename = f"{str(uuid.uuid4())}{file_extension}"
    return unique_filename


def allowed_file(filename, allowed_extensions=None):
    """Check if file has an allowed extension"""
    if allowed_extensions is None:
        allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', set())
        
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions
