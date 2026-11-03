import os
import sys

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('pronostix')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# En la suite de tests no hay Redis: ejecutar las tareas en proceso.
if 'test' in sys.argv or os.getenv('CELERY_TASK_ALWAYS_EAGER', '0') == '1':
    app.conf.task_always_eager = True
    app.conf.task_eager_propagates = True
    app.conf.broker_url = 'memory://'
    app.conf.result_backend = 'cache+memory://'
