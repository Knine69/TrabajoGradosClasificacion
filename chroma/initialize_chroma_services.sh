#!/bin/bash_files

source /chroma_app/.chroma/bin/activate
gunicorn -c chroma/gunicorn.conf.py 'chroma:create_app()' & \
celery -A chroma worker --loglevel=info --time-limit=50 --soft-time-limit=30 -Q chroma_queue --hostname=chroma@%h