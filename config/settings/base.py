"""
Django settings for config project.

Generated by 'django-admin startproject' using Django 3.2.6.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""
import base64
import os
from collections import OrderedDict
from datetime import timedelta

from config.constants.error_messages import ERROR_MESSAGES

# Build paths inside the project like this: BASE_DIR / 'subdir'.

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'm$*!s$%=a1e685t@h#34%!-!(q5(q=lj0bdlgh&ewv)*u3#nz6'
ENCRYPTION_KEY = 'S3&ewm85t=a1e6@h$*!s$d%#v)*4%!-!(q5(q=lj0bdlghu3#nz6'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

HOTP_KEY = base64.b32encode(SECRET_KEY.encode("utf-8"))
OTP_LENGTH = 4
OTP_VALIDITY_PERIOD = 90  # in seconds

SITE_URL = os.getenv('SITE_URL', '127.0.0.1:8000')
DEV_MODE = bool(os.getenv('DEV_MODE', 1))

TG_AUTH_BOT_USERNAME = os.getenv('TG_AUTH_BOT_USERNAME')
TG_AUTH_BOT_HOST = os.getenv('TG_AUTH_BOT_HOST', 'http://gp-tgauth-bot:3113')

# RABBITMQ_HOST_SERVER = 'localhost'
# RABBITMQ_USER = 'user'
# RABBITMQ_PASSWORD = 'user'
# RABBITMQ_PORT = '5672/%2F'
# RABBITMQ_HOST_LOCAL = '185.100.67.155'

# Redis settings
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
# REDIS_HOST = "localhost"
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_DB_FOR_CELERY = os.getenv("REDIS_DB_FOR_CELERY", "0")
REDIS_DB_FOR_CACHE = os.getenv("REDIS_DB_FOR_CACHE", "1")
REDIS_AS_CACHE_URL = "redis://{host}:{port}/{db_index}".format(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db_index=REDIS_DB_FOR_CACHE,
)
REDIS_AS_BROKER_URL = "redis://{host}:{port}/{db_index}".format(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db_index=REDIS_DB_FOR_CELERY,
)

SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'api_key': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization'
        }
    },
}

CONSTANCE_BACKEND = 'constance.backends.database.DatabaseBackend'

CONSTANCE_CONFIG = {
    **ERROR_MESSAGES,
    "EXCEPTION_HANDLING_STATUS": (True, "Статус отлавливания исключений", bool),
    "USE_DEFAULT_OTP": (True, "Использовать код по умолчанию", bool),
    "DEFAULT_OTP": ("1111", "Код по умолчанию", str),
    "FREE_SECONDS_BEFORE_START_TARIFFING": (0, "Бесплатное время перед началом тарификации (сек)", int),
    "PAYMENT_EXPIRY_TIME": (5, "Время на оплату (мин)", int),
    "MULTIBOOKING_LAUNCHING_TIME": (10, "Время, которое компьютеры еще показываются недоступными в приле (мин)", int),
    "INTEGRATIONS_TURNED_ON": (False, "Включить интеграции с Gizmo", bool),
    "GAMER_PRO_COMMISSION": (100, "Наша комиссия в тенге", int),
    "CASHBACK_TURNED_ON": (True, "Включить кэшбеки", bool),
    "CASHBACK_PERCENT": (5, "% кэшбека от суммы транзакции", int),
    "EXTRA_MINUTES_TO_FIRST_TRANSACTION": (60, "Экстра минуты бесплатно для первой транзакции", int),
    "KASPI_PAYMENT_SERVICE_CODE": ("BRO", "SERVICE CODE для сервиса оплаты через Каспи банк", str),
    "KASPI_PAYMENT_SERVICE_CODE_LOBBY": ("LOBBY", "SERVICE CODE для сервиса оплаты через Каспи банк для LOBBY", str),
    "KASPI_PAYMENT_DEEPLINK_HOST": (
        "https://server.gamerpro.kz", "Диплинк для возвращения в прилу после успешной оплаты", str
    ),
    "COMPUTER_UNLOCK_DELAY": (5, "Задержка разблокировки компьютера (мин)", int),
}

CONSTANCE_CONFIG_FIELDSETS = OrderedDict([
    ("Settings", ("INTEGRATIONS_TURNED_ON",)),
    ("Billing", (
        "FREE_SECONDS_BEFORE_START_TARIFFING",
        "PAYMENT_EXPIRY_TIME",
        "MULTIBOOKING_LAUNCHING_TIME",
        "GAMER_PRO_COMMISSION",
        "CASHBACK_TURNED_ON",
        "CASHBACK_PERCENT",
        "EXTRA_MINUTES_TO_FIRST_TRANSACTION",
        "KASPI_PAYMENT_SERVICE_CODE",
        "KASPI_PAYMENT_SERVICE_CODE_LOBBY",
        "KASPI_PAYMENT_DEEPLINK_HOST",
    )),
    ("OTP settings", ("USE_DEFAULT_OTP", "DEFAULT_OTP",)),
    ("Computers", ("COMPUTER_UNLOCK_DELAY",)),
    ("Exception Handling", ("EXCEPTION_HANDLING_STATUS",)),
    ("Error messages", tuple(ERROR_MESSAGES.keys())),
])
CONSTANCE_IGNORE_ADMIN_VERSION_CHECK = True

CONSTANCE_REDIS_CONNECTION = {
    'host': REDIS_HOST,
    'port': REDIS_PORT,
    'db': REDIS_DB_FOR_CACHE,
}

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    # "django_filters",
    "corsheaders",
    "phonenumber_field",
    "constance",
    "constance.backends.database",
    "django_celery_beat",
    "django_json_widget",
    # "ckeditor",
    # "ckeditor_uploader",
]

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

LOCAL_APPS = [
    'apps.authentication.apps.AuthenticationConfig',
    'apps.common.apps.CommonConfig',
    'apps.users.apps.UsersConfig',
    'apps.integrations.apps.IntegrationsConfig',
    'apps.clubs.apps.ClubsConfig',
    'apps.bookings.apps.BookingsConfig',
    'apps.notifications.apps.NotificationsConfig',
    'apps.payments.apps.PaymentsConfig',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

AUTH_USER_MODEL = "users.User"

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    "corsheaders.middleware.CorsMiddleware",
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

SETTINGS_PATH = os.path.dirname(os.path.dirname(__file__))
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(SETTINGS_PATH, "..", "templates")],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.server.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        "NAME": os.getenv("DB_NAME", "gamerprodb"),
        "USER": os.getenv("DB_USER", "gamerprodb"),
        "PASSWORD": os.getenv("DB_PASSWORD", "gamerprodb"),
        "HOST": os.getenv("DB_HOST", "gp-postgres"),
        # "HOST": "localhost",
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'access-control-allow-origin',
    'accept',
    'accept-encoding',
    'accept-language',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'x-api-key',
    'cookie'
]

USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'ru'
TIME_ZONE = "Asia/Almaty"

USE_I18N = True
USE_L10N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

DATA_UPLOAD_MAX_NUMBER_FIELDS = None

STATIC_URL = "static/"
STATIC_ROOT = os.path.join(PROJECT_DIR, "..", 'static')
# STATIC_DIR = os.path.join(BASE_DIR, 'static')
# STATICFILES_DIRS = [STATIC_DIR]
MEDIA_URL = "media/"
MEDIA_ROOT = os.path.join(PROJECT_DIR, "..", "media")

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
SITE_DOMAIN = "http://127.0.0.1:8008"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = os.getenv("SMTP_PORT")
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")

REST_FRAMEWORK = {
    # "DEFAULT_AUTHENTICATION_CLASSES": [
    #     "apps.users.authentication.JWTAuthentication"
    # ],
    "DEFAULT_AUTHENTICATION_CLASSES": ('apps.authentication.authentication.SafeJWTAuthentication',),
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DATETIME_FORMAT": "%Y-%m-%dT%H:%M",
    # "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "DEFAULT_PAGINATION_CLASS": "apps.common.pagination.CustomPagination",
    "PAGE_SIZE": 100,
    'COERCE_DECIMAL_TO_STRING': False,
    'DEFAULT_VERSIONING_CLASS': 'apps.common.versioning.HeaderVersioning',
    'DEFAULT_VERSION': '1.0'
}


SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=70),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": False,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "VERIFYING_KEY": None,
    "AUTH_HEADER_TYPES": ("JWT",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
}


CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_AS_CACHE_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

# Celery settings

CELERY_BROKER_URL = REDIS_AS_BROKER_URL
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers.DatabaseScheduler"

CELERY_RESULT_EXTENDED = False
CELERY_RESULT_EXPIRES = 3600
CELERY_ALWAYS_EAGER = False
CELERY_ACKS_LATE = True
CELERY_TASK_PUBLISH_RETRY = False
CELERY_DISABLE_RATE_LIMITS = False
CELERY_TASK_TRACK_STARTED = True

ONE_VISION_LIBERTY_API_KEY = os.getenv("ONE_VISION_LIBERTY_API_KEY")
ONE_VISION_LIBERTY_API_SECRET_KEY = os.getenv("ONE_VISION_LIBERTY_API_SECRET_KEY")

ONE_VISION_BRO_API_KEY = os.getenv("ONE_VISION_BRO_API_KEY")
ONE_VISION_BRO_API_SECRET_KEY = os.getenv("ONE_VISION_BRO_API_SECRET_KEY")

# CKEDITOR_UPLOAD_PATH = "ncrm_helper"

LOGFILE_SIZE = 1024 * 1024 * 5
LOGFILE_COUNT = 10

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s -- %(asctime)s -- %(message)s',
        },
        'simple': {
            'format': '%(levelname)s -- %(message)s',
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        # 'users_file': {
        #     'level': 'INFO',
        #     'class': 'logging.handlers.RotatingFileHandler',
        #     'filename': os.path.join(BASE_DIR, 'logs') + '/users/users.log',
        #     'maxBytes': LOGFILE_SIZE,
        #     'backupCount': LOGFILE_COUNT,
        #     'formatter': 'verbose'
        # },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'propagate': True,
        },
        'users': {
            'handlers': [
                'console',
                # 'users_file'
            ],
            'level': 'INFO',
            'propagate': True,
        },
        'notifications': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'gizmo': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'senet': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'onevision': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'integrations': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        }
    }
}

JARYQLAB_API_KEY = os.getenv("JARYQLAB_API_KEY")
