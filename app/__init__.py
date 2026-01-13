"""
Flask application factory for Radar - Enterprise Competitor Intelligence Platform.

This module implements the application factory pattern to allow flexible
configuration and testing. All Flask extensions are initialized here.
"""

from flask import Flask
from flask_cors import CORS
import logging
from datetime import datetime

from app.config import Config
from app.extensions import (
    db,
    redis_client,
    celery,
    jwt,
    login_manager,
    csrf,
    limiter
)
from app.utils.logging import setup_logging


def create_app(config_class=Config):
    """
    Application factory pattern for Flask.
    
    Args:
        config_class: Configuration class to use (default: Config)
        
    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize logging first
    setup_logging(app)
    logger = logging.getLogger(__name__)
    logger.info("Initializing Radar application")
    
    # Initialize security manager
    from app.utils.security import init_security_manager
    init_security_manager(app.config['ENCRYPTION_KEY'])
    
    # Initialize extensions
    db.init_app(app)
    redis_client.init_app(app)
    
    # Initialize Celery with Flask context
    celery.conf.update(
        broker_url=app.config['CELERY_BROKER_URL'],
        result_backend=app.config['CELERY_RESULT_BACKEND'],
        task_serializer=app.config['CELERY_TASK_SERIALIZER'],
        accept_content=app.config['CELERY_ACCEPT_CONTENT'],
        result_serializer=app.config['CELERY_RESULT_SERIALIZER'],
        timezone=app.config['CELERY_TIMEZONE'],
        enable_utc=app.config['CELERY_ENABLE_UTC'],
        task_track_started=app.config['CELERY_TASK_TRACK_STARTED'],
        task_time_limit=app.config['CELERY_TASK_TIME_LIMIT'],
        task_soft_time_limit=app.config['CELERY_TASK_SOFT_TIME_LIMIT']
    )
    
    class ContextTask(celery.Task):
        """Make celery tasks work with Flask app context."""
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    
    jwt.init_app(app)
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        """Load user for Flask-Login."""
        from app.auth.models import User
        return User.query.get(user_id)
    
    csrf.init_app(app)
    
    # Initialize rate limiter with Redis storage
    limiter.storage_uri = app.config['RATELIMIT_STORAGE_URL']
    limiter.init_app(app)
    
    # CORS configuration (restrictive for security)
    CORS(
        app,
        origins=app.config.get('ALLOWED_ORIGINS', []),
        supports_credentials=True,
        methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
        allow_headers=['Content-Type', 'Authorization', 'X-CSRFToken']
    )
    
    # Register blueprints (lazy import to avoid circular dependencies)
    # Blueprints will be imported when routes are registered
    # Register blueprints (lazy import to avoid circular dependencies)
    try:
        from app.auth.routes import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/api/auth')
    except ImportError as e:
        logger.warning(f"Auth blueprint not available: {str(e)}")
    
    try:
        from app.companies.routes import companies_bp
        app.register_blueprint(companies_bp, url_prefix='/api/companies')
    except ImportError as e:
        logger.warning(f"Companies blueprint not available: {str(e)}")
    
    try:
        from app.reports.routes import reports_bp
        app.register_blueprint(reports_bp, url_prefix='/api/reports')
    except ImportError as e:
        logger.warning(f"Reports blueprint not available: {str(e)}")
    
    try:
        from app.dashboard.routes import dashboard_bp
        app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    except ImportError as e:
        logger.warning(f"Dashboard blueprint not available: {str(e)}")
    
    try:
        from app.scheduling.routes import scheduling_bp
        app.register_blueprint(scheduling_bp, url_prefix='/api/scheduling')
    except ImportError as e:
        logger.warning(f"Scheduling blueprint not available: {str(e)}")
    
    # Register error handlers
    from app.utils.error_handlers import register_error_handlers
    register_error_handlers(app)
    
    # Import models for database initialization
    from app.auth.models import User, PasswordResetToken
    from app.companies.models import Company, Competitor, TrackingConfig
    from app.intelligence.models import IntelligenceData, Startup
    from app.reports.models import Report
    
    # Create database tables
    with app.app_context():
        db.create_all()
        logger.info("Database tables initialized")
    
    logger.info("Radar application initialized successfully")
    
    return app
