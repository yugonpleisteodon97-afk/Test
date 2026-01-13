"""
Structured logging configuration for Radar application.

Provides Sentry-ready logging format and structured log output
for production monitoring and debugging.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from flask import Flask
import json
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.
    
    Outputs logs in JSON format compatible with log aggregation systems
    (ELK, Splunk, CloudWatch, etc.) and Sentry.
    """
    
    def format(self, record):
        """
        Format log record as JSON.
        
        Args:
            record: LogRecord instance
            
        Returns:
            JSON-formatted log string
        """
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        if hasattr(record, 'company_id'):
            log_data['company_id'] = record.company_id
        
        return json.dumps(log_data)


def setup_logging(app: Flask):
    """
    Configure logging for Flask application.
    
    Sets up both file and console logging with appropriate formatters
    based on environment (JSON for production, human-readable for development).
    
    Args:
        app: Flask application instance
    """
    # Get log level from config
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO').upper(), logging.INFO)
    
    # Remove default handlers
    app.logger.handlers = []
    
    # Console handler (always add)
    console_handler = logging.StreamHandler(sys.stdout)
    if app.config.get('ENV') == 'production':
        # JSON format for production
        console_handler.setFormatter(JSONFormatter())
    else:
        # Human-readable format for development
        console_handler.setFormatter(
            logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        )
    console_handler.setLevel(log_level)
    app.logger.addHandler(console_handler)
    
    # File handler (if log file is configured)
    log_file = app.config.get('LOG_FILE')
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        # Always use JSON format for file logs
        file_handler.setFormatter(JSONFormatter())
        file_handler.setLevel(log_level)
        app.logger.addHandler(file_handler)
    
    # Set application logger level
    app.logger.setLevel(log_level)
    
    # Suppress noisy third-party loggers
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('celery').setLevel(logging.WARNING)
    
    # Initialize Sentry if DSN is provided
    sentry_dsn = app.config.get('SENTRY_DSN')
    if sentry_dsn:
        try:
            import sentry_sdk
            from sentry_sdk.integrations.flask import FlaskIntegration
            from sentry_sdk.integrations.celery import CeleryIntegration
            from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
            
            sentry_sdk.init(
                dsn=sentry_dsn,
                integrations=[
                    FlaskIntegration(),
                    CeleryIntegration(),
                    SqlalchemyIntegration()
                ],
                traces_sample_rate=0.1,  # 10% of transactions
                environment=app.config.get('ENV', 'development'),
                release=app.config.get('VERSION', '1.0.0')
            )
            app.logger.info("Sentry initialized successfully")
        except ImportError:
            app.logger.warning("Sentry DSN provided but sentry-sdk not installed")
        except Exception as e:
            app.logger.error(f"Failed to initialize Sentry: {str(e)}")


def get_logger(name: str) -> logging.Logger:
    """
    Get logger instance with consistent naming.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
