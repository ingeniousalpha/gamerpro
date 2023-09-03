from config.celery_app import cel_app


# @cel_app.task(bind=True, ignore_result=True, base=BaseTaskWithInfRetry)
# def push_broadcast_task(message_type, data, extra_data=None):
#     """Отправить push-уведомление на все токены из БД"""
#
#     messages = [
#         messaging.Message(
#             notification=messaging.Notification(title=data[key]['title'], body=data[key]['body']),
#             android=messaging.AndroidConfig(priority='high'),
#             apns=messaging.APNSConfig(
#                 headers={"apns-priority": "10"},
#                 payload=messaging.APNSPayload(aps=messaging.Aps(sound='default'))
#             ),
#             topic=key.upper(),
#             data=extra_data
#         ) for key in data
#     ]
#
#     response = messaging.send_all(messages)
#     logger.info(f"Completed: {response.success_count}. Failed: {response.failure_count}.")
#
#     if response.failure_count > 0 and response.responses:
#         for index, resp in enumerate(response.responses):
#             logger.error(f"Error[{index}]: {resp.exception}")

