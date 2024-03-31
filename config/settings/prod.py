from .base import *

SITE_DOMAIN = "https://gamerpro.kz"
FCM_CREDENTIALS_PATH = "/credentials/fcm-prod.json"

REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
REDIS_AS_CACHE_URL = "redis://:{password}@{host}:{port}/{db_index}".format(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    db_index=REDIS_DB_FOR_CACHE,
)
REDIS_AS_BROKER_URL = "redis://:{password}@{host}:{port}/{db_index}".format(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    db_index=REDIS_DB_FOR_CELERY,
)
CONSTANCE_REDIS_CONNECTION = REDIS_AS_CACHE_URL
CACHES['default']['LOCATION'] = REDIS_AS_CACHE_URL
CELERY_BROKER_URL = REDIS_AS_BROKER_URL
