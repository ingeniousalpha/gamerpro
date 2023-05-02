import os
from celery import Celery
from celery.schedules import crontab

if not ("DJANGO_SETTINGS_MODULE" in os.environ):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

cel_app = Celery("gamerpro")

cel_app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs.
cel_app.autodiscover_tasks()

cel_app.conf.beat_schedule = {
    'synchronize-gizmo-computers-state': {
        'task': 'apps.clubs.tasks.synchronize_gizmo_computers_state',
        'schedule': crontab(minute='*')
    },
}