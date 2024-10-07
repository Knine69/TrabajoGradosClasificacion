from celery import Celery
from app_config import Configuration

celery = Celery()


def celery_instantiation(app):
    celery.conf.update({
        'broker_url': Configuration.CELERY_BROKER_URL,
        'result_backend': Configuration.CELERY_RESULT_BACKEND,
        'task_serializer': 'json',
        'result_serializer': 'json',
        'accept_content': ['json'],
        'timezone': 'UTC',
        'enable_utc': True,
        'task_queues': {
            app.config.get('CHROMA_QUEUE', 'chroma_queue'): {
                'exchange': 'chroma_exchange',
                'routing_key': 'chroma.#',
            },
        },
    })

    class ContextTask(celery.Task):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return super().__call__(self, *args, **kwargs)

    celery.Task = ContextTask
