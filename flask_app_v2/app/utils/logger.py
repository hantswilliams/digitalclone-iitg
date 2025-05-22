"""
Centralized logging configuration
"""
import logging
from flask import has_request_context, request, g
from logging.handlers import RotatingFileHandler
import os
import json
from datetime import datetime


class RequestFormatter(logging.Formatter):
    """Formatter that includes request info in logs when available"""
    
    def format(self, record):
        if has_request_context():
            record.url = request.url
            record.remote_addr = request.remote_addr
            record.method = request.method
            record.path = request.path
            
            # Add user information if available
            if hasattr(g, 'user'):
                record.user_id = g.user.id
            else:
                record.user_id = 'anonymous'
        else:
            record.url = None
            record.remote_addr = None
            record.method = None
            record.path = None
            record.user_id = None
            
        return super().format(record)


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging
    """
    
    def format(self, record):
        """Format log record as JSON"""
        log_record = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        
        # Add exception info if available
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)
            
        # Add request context if available
        if has_request_context():
            log_record.update({
                'request': {
                    'url': request.url,
                    'method': request.method,
                    'ip': request.remote_addr,
                    'path': request.path,
                }
            })
            
            # Add user agent if available
            if request.user_agent:
                log_record['request']['user_agent'] = request.user_agent.string
                
            # Add user ID if available
            if hasattr(g, 'user'):
                log_record['user_id'] = g.user.id
                
        # Add custom attributes
        for key, value in record.__dict__.items():
            if key not in ('args', 'asctime', 'created', 'exc_info', 'exc_text', 
                          'filename', 'funcName', 'id', 'levelname', 'levelno', 
                          'lineno', 'module', 'msecs', 'message', 'msg', 
                          'name', 'pathname', 'process', 'processName', 
                          'relativeCreated', 'stack_info', 'thread', 'threadName'):
                try:
                    # Try to serialize to JSON, skip if not possible
                    json.dumps({key: value})
                    log_record[key] = value
                except (TypeError, OverflowError):
                    log_record[key] = str(value)
                    
        return json.dumps(log_record)


def configure_logger(app):
    """Configure application logger with file and console handlers"""
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(app.root_path, '..', 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    # Clean up existing handlers to avoid duplicates in development
    if app.debug:
        for handler in list(app.logger.handlers):
            app.logger.removeHandler(handler)
    
    # Set up file handler for error logs
    error_log_file = os.path.join(logs_dir, 'error.log')
    error_file_handler = RotatingFileHandler(
        error_log_file, maxBytes=10485760, backupCount=10
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(RequestFormatter(
        '[%(asctime)s] [%(user_id)s] %(remote_addr)s - "%(method)s %(path)s" '
        '%(levelname)s in %(module)s: %(message)s'
    ))
    app.logger.addHandler(error_file_handler)
    
    # Set up file handler for general logs
    info_log_file = os.path.join(logs_dir, 'info.log')
    info_file_handler = RotatingFileHandler(
        info_log_file, maxBytes=10485760, backupCount=10
    )
    info_file_handler.setLevel(logging.INFO)
    info_file_handler.setFormatter(RequestFormatter(
        '[%(asctime)s] [%(user_id)s] %(remote_addr)s - "%(method)s %(path)s" '
        '%(levelname)s: %(message)s'
    ))
    app.logger.addHandler(info_file_handler)
    
    # Set up JSON structured logging
    json_log_file = os.path.join(logs_dir, 'app.json.log')
    json_file_handler = RotatingFileHandler(
        json_log_file, maxBytes=10485760, backupCount=10
    )
    json_file_handler.setLevel(logging.INFO)
    json_file_handler.setFormatter(JSONFormatter())
    app.logger.addHandler(json_file_handler)
    
    # Set up console handler with colored output for development
    console_handler = logging.StreamHandler()
    if app.debug:
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(logging.Formatter(
            '\033[92m%(asctime)s\033[0m \033[94m%(levelname)s\033[0m: %(message)s '
            '[in \033[95m%(pathname)s:%(lineno)d\033[0m]'
        ))
    else:
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
    app.logger.addHandler(console_handler)
    
    # Set overall logging level
    if app.debug:
        app.logger.setLevel(logging.DEBUG)
    else:
        app.logger.setLevel(logging.INFO)
        
    app.logger.info('Enhanced logging system initialized')
    
    return app.logger
