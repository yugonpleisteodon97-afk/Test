web: gunicorn --bind 0.0.0.0:$PORT --workers 4 --timeout 120 wsgi:app
worker: celery -A app.extensions.celery worker --loglevel=info
beat: celery -A app.extensions.celery beat --loglevel=info
