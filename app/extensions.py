"""
Flask extension initialization.

All Flask extensions are instantiated here to avoid circular imports.
Extensions are initialized in app/__init__.py after app creation.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_redis import FlaskRedis
from celery import Celery
from flask_jwt_extended import JWTManager
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


# Database
db = SQLAlchemy()

# Redis (for caching and rate limiting)
redis_client = FlaskRedis(decode_responses=True)

# Celery (for background tasks)
celery = Celery(__name__)

# JWT Manager
jwt = JWTManager()

# Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'
login_manager.session_protection = 'strong'

# CSRF Protection
csrf = CSRFProtect()

# Rate Limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per hour"],
    storage_uri=None  # Will be set in app initialization
)
