"""
Configuration management for Radar application.

Supports environment-based configuration (development, staging, production)
with secure defaults and environment variable overrides.
"""

import os
from datetime import timedelta
from pathlib import Path


class Config:
    """Base configuration with secure defaults."""
    
    # Application
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(32).hex()
    APP_NAME = 'Radar'
    VERSION = '1.0.0'
    PORT = int(os.environ.get('PORT', 5000))
    
    # Database
    # Railway provides DATABASE_URL, but SQLAlchemy 1.4+ requires postgresql:// not postgres://
    DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://radar_user:radar_pass@localhost:5432/radar_db')
    if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'max_overflow': 20,
        'echo': False
    }
    
    # Redis
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    REDIS_CACHE_TTL = int(os.environ.get('REDIS_CACHE_TTL', '3600'))
    
    # Celery
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', REDIS_URL.replace('/0', '/1'))
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', REDIS_URL.replace('/0', '/2'))
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_TIMEZONE = 'UTC'
    CELERY_ENABLE_UTC = True
    CELERY_TASK_TRACK_STARTED = True
    CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
    CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes
    
    # JWT
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_TOKEN_LOCATION = ['headers', 'cookies']
    JWT_COOKIE_SECURE = True
    JWT_COOKIE_HTTPONLY = True
    JWT_COOKIE_SAMESITE = 'Lax'
    
    # Flask-Login
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = timedelta(days=30)
    
    # Security
    BCRYPT_LOG_ROUNDS = 12
    CSRF_ENABLED = True
    CSRF_TIME_LIMIT = 3600
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION = timedelta(minutes=15)
    
    # Rate Limiting
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URL = REDIS_URL
    RATELIMIT_DEFAULT = "200 per hour"
    RATELIMIT_STRATEGY = "fixed-window"
    
    # CORS
    ALLOWED_ORIGINS = os.environ.get(
        'ALLOWED_ORIGINS',
        'http://localhost:5000,http://127.0.0.1:5000'
    ).split(',')
    
    # Security Headers
    SECURITY_HEADERS = {
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Content-Security-Policy': "default-src 'self'"
    }
    
    # Encryption (Fernet)
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY') or os.urandom(32).hex()
    
    # OAuth
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    MICROSOFT_CLIENT_ID = os.environ.get('MICROSOFT_CLIENT_ID')
    MICROSOFT_CLIENT_SECRET = os.environ.get('MICROSOFT_CLIENT_SECRET')
    OAUTH_REDIRECT_URI = os.environ.get('OAUTH_REDIRECT_URI', 'http://localhost:5000/api/auth/oauth/callback')
    
    # API Keys (encrypted at rest)
    ALPHA_VANTAGE_API_KEY = os.environ.get('ALPHA_VANTAGE_API_KEY')
    FINNHUB_API_KEY = os.environ.get('FINNHUB_API_KEY')
    CRUNCHBASE_API_KEY = os.environ.get('CRUNCHBASE_API_KEY')
    SIMILARWEB_API_KEY = os.environ.get('SIMILARWEB_API_KEY')
    NEWS_API_KEY = os.environ.get('NEWS_API_KEY')
    THE_NEWS_API_KEY = os.environ.get('THE_NEWS_API_KEY')
    TWITTER_API_KEY = os.environ.get('TWITTER_API_KEY')
    TWITTER_API_SECRET = os.environ.get('TWITTER_API_SECRET')
    TWITTER_BEARER_TOKEN = os.environ.get('TWITTER_BEARER_TOKEN')
    SERPAPI_API_KEY = os.environ.get('SERPAPI_API_KEY')
    
    # File Storage
    UPLOAD_FOLDER = Path(os.environ.get('UPLOAD_FOLDER', './storage/reports'))
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Report Generation
    REPORT_TEMPLATE_DIR = Path(__file__).parent / 'reports' / 'templates'
    REPORT_OUTPUT_DIR = UPLOAD_FOLDER / 'pdfs'
    CHART_OUTPUT_DIR = UPLOAD_FOLDER / 'charts'
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
    LOG_FILE = os.environ.get('LOG_FILE', './logs/radar.log')
    SENTRY_DSN = os.environ.get('SENTRY_DSN')
    
    # Monitoring
    ENABLE_METRICS = os.environ.get('ENABLE_METRICS', 'false').lower() == 'true'
    PROMETHEUS_PORT = int(os.environ.get('PROMETHEUS_PORT', '9090'))
    
    @staticmethod
    def init_app(app):
        """Initialize application with configuration."""
        # Create necessary directories
        for directory in [
            app.config['UPLOAD_FOLDER'],
            app.config['REPORT_OUTPUT_DIR'],
            app.config['CHART_OUTPUT_DIR'],
            Path(app.config['LOG_FILE']).parent
        ]:
            directory.mkdir(parents=True, exist_ok=True)


class DevelopmentConfig(Config):
    """Development configuration with relaxed security for local development."""
    DEBUG = True
    TESTING = False
    JWT_COOKIE_SECURE = False  # Allow HTTP in development
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False
    CSRF_ENABLED = True  # Still enforce CSRF even in dev


class StagingConfig(Config):
    """Staging configuration with production-like settings."""
    DEBUG = False
    TESTING = False
    LOG_LEVEL = 'WARNING'


class ProductionConfig(Config):
    """Production configuration with maximum security."""
    DEBUG = False
    TESTING = False
    LOG_LEVEL = 'ERROR'
    
    # Override with strict security
    ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', '').split(',')
    if not ALLOWED_ORIGINS or ALLOWED_ORIGINS == ['']:
        raise ValueError("ALLOWED_ORIGINS must be set in production")


class TestingConfig(Config):
    """Testing configuration with in-memory database."""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    REDIS_URL = 'redis://localhost:6379/15'  # Separate DB for tests
    CELERY_BROKER_URL = 'redis://localhost:6379/15'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379/15'
    JWT_COOKIE_SECURE = False
    SESSION_COOKIE_SECURE = False
    CSRF_ENABLED = False
    WTF_CSRF_ENABLED = False


# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'staging': StagingConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
