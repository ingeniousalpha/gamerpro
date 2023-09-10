import os
import logging

from django.conf import settings
from firebase_admin import credentials, initialize_app, messaging

from apps.notifications import BaseTaskWithRetry
from config.celery_app import cel_app

logger = logging.getLogger("notifications")

current_path = os.path.dirname(__file__)
cred = credentials.Certificate(current_path + settings.FCM_CREDENTIALS_PATH)
initialize_app(cred)


@cel_app.task(bind=True, ignore_result=True, base=BaseTaskWithRetry)
def fcm_subscribe_topic(tokens, topic):
    """Подписать firebase-токен(ы) на топик"""

    if isinstance(tokens, str):
        tokens = [tokens]

    messaging.subscribe_to_topic(tokens, topic.upper())


@cel_app.task(bind=True, ignore_result=True, base=BaseTaskWithRetry)
def fcm_unsubscribe_topic(tokens, topic):
    """Отписать firebase-токен(ы) на топик"""

    if isinstance(tokens, str):
        tokens = [tokens]

    messaging.unsubscribe_from_topic(tokens, topic.upper())


@cel_app.task(bind=True, ignore_result=True, base=BaseTaskWithRetry)
def fcm_push_broadcast(data, extra_data=None):
    """Отправить push-уведомление на все токены из БД"""

    messages = [
        messaging.Message(
            notification=messaging.Notification(title=data[key]['title'], body=data[key]['body']),
            android=messaging.AndroidConfig(priority='high'),
            apns=messaging.APNSConfig(
                headers={"apns-priority": "10"},
                payload=messaging.APNSPayload(aps=messaging.Aps(sound='default'))
             ),
            topic=key.upper(),
            data=extra_data
        ) for key in data
    ]

    response = messaging.send_each(messages)
    logger.info(f"Completed: {response.success_count}. Failed: {response.failure_count}.")

    if response.failure_count > 0 and response.responses:
        for index, resp in enumerate(response.responses):
            logger.error(f"Error[{index}]: {resp.exception}")


@cel_app.task(bind=True, ignore_result=True, base=BaseTaskWithRetry)
def fcm_push_notify_user(tokens, data, extra_data):
    """Отправить push-уведомление на определенный список токенов"""

    if tokens:
        message = messaging.MulticastMessage(
            notification=messaging.Notification(title=data["title"], body=data["body"]),
            android=messaging.AndroidConfig(priority='high'),
            apns=messaging.APNSConfig(
                headers={"apns-priority": "10"},
                payload=messaging.APNSPayload(aps=messaging.Aps(sound='default'))
            ),
            data=extra_data,
            tokens=tokens
        )

        response = messaging.send_each_for_multicast(message)
        logger.info(f"Completed: {response.success_count}. Failed: {response.failure_count}.")

        if response.failure_count > 0 and response.responses:
            for index, resp in enumerate(response.responses):
                logger.error(f"Error[{index}]: {resp.exception}")
