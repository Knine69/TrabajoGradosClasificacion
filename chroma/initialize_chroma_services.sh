#!/bin/bash_files

gunicorn -c chroma/gunicorn.conf.py 'chroma:create_app()' && \
celery -A chroma worker --loglevel=info --time-limit=50 --soft-time-limit=30 \
-Q chroma_queue --hostname=chroma@%h