#!/bin/bash_files

source /langchain_app/.langchain/bin/activate
gunicorn -c user_langchain/gunicorn.conf.py 'user_langchain:create_app()' & \
celery -A user_langchain worker --loglevel=debug  -Q langchain_queue -n langchain@%n
