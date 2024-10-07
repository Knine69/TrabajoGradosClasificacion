#!/bin/bash

# Start Gunicorn in the background
gunicorn -c chroma/gunicorn.conf.py 'chroma:create_app()' & \
# Start Celery worker in the foreground
celery -A chroma worker --loglevel=info --time-limit=50 --soft-time-limit=30 -Q chroma_queue --hostname=chroma@%h
