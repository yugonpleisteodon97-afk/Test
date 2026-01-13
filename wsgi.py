"""
WSGI entry point for Gunicorn.

This module creates the Flask application instance for production deployment.
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run()
