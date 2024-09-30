import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Configuration:

    RABBIT_BROKER_URL = os.getenv('RABBIT_BROKER_URL',
                                  'pyamqp://guest@rabbitmq//')
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND',
                                      'redis://redis:6379/0')
    LANGCHAIN_QUEUE = os.getenv('LANGCHAIN_QUEUE', 'langchain_queue')
    CHROMA_QUEUE = os.getenv('CHROMA_QUEUE', 'chroma_queue')
