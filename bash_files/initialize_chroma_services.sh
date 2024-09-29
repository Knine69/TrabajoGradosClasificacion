#!/bin/bash_files

source .chroma/bin/activate
pip install -r chroma/requirements.txt
mkdir bash_files/chroma_server
chmod -R 755 bash_files/chroma_server
chroma run --path bash_files/chroma_server --host localhost --port $1 &\
gunicorn -c chroma/gunicorn.conf.py 'chroma:create_app()' &\
celery -A chroma worker --loglevel=info --time-limit=50 --soft-time-limit=30 -Q chroma_queue --hostname=chroma@%h