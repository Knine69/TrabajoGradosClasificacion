import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Configuration:

    RABBIT_BROKER_URL = os.getenv('RABBIT_BROKER_URL')
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND')
    LANGCHAIN_QUEUE = os.getenv('LANGCHAIN_QUEUE', 'langchain_queue')
    CHROMA_QUEUE = os.getenv('CHROMA_QUEUE', 'chroma_queue')
