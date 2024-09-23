from celery import Celery

celery = Celery()


def celery_instantiation(app):
    celery.conf.update({
        'broker_url': app.config['RABBIT_BROKER_URL'],
        'result_backend': app.config['CELERY_RESULT_BACKEND'],
        'task_serializer': 'json',
        'result_serializer': 'json',
        'accept_content': ['json'],
        'timezone': 'UTC',
        'enable_utc': True,
    })

    class ContextTask(celery.Task):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return super().__call__(self, *args, **kwargs)

    celery.Task = ContextTask