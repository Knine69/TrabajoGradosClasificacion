#!/bin/bash_files

source .langchain/bin/activate
pip install -r user_langchain/requirements.txt
gunicorn -c user_langchain/gunicorn.conf.py 'user_langchain:create_app()' &\
celery -A user_langchain worker --loglevel=info --time-limit=50 --soft-time-limit=30 -Q langchain_queue --hostname=langchain