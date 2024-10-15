import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Configuration:

    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL',
                                  'pyamqp://guest@rabbitmq//')
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND',
                                      'redis://redis:6379/0')
    REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
    LANGCHAIN_QUEUE = os.getenv('LANGCHAIN_QUEUE', 'langchain_queue')
    CHROMA_QUEUE = os.getenv('CHROMA_QUEUE', 'chroma_queue')
    CHROMA_URL = os.getenv('CHROMA_URL', 'chroma')
