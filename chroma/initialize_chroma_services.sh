#!/bin/bash


gunicorn -c chroma/gunicorn.conf.py 'chroma:create_app()' & \
celery -A chroma worker --loglevel=info -Q chroma_queue --hostname=chroma@%h
