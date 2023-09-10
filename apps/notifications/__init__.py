from celery import Task
import psycopg2

from .exceptions import RetryTaskException
default_app_config = 'apps.notifications.apps.NotificationsConfig'


class BaseTaskWithRetry(Task):
    autoretry_for = (Exception, RetryTaskException, psycopg2.OperationalError)
    max_retries = 5
    retry_backoff = True
    retry_backoff_max = 30
    retry_jitter = True