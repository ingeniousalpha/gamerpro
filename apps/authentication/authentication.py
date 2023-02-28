import jwt
import logging
from django.conf import settings
from django.contrib.auth import user_logged_in
from django.middleware.csrf import CsrfViewMiddleware
from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions

# Get an instance of a logger
logger = logging.getLogger("users")


class CSRFCheck(CsrfViewMiddleware):
    def _reject(self, request, reason):
        # Return the failure reason instead of an HttpResponse
        return reason


class SafeJWTAuthentication(BaseAuthentication):
    """
        custom authentication class for DRF and JWT
        https://github.com/encode/django-rest-framework/blob/master/rest_framework/authentication.py
    """

    def authenticate(self, request):

        from apps.users.models import User

        authorization_header = request.headers.get('Authorization')

        if not authorization_header:
            return None
        try:
            # header = 'Token xxxxxxxxxxxxxxxxxxxxxxxx'
            access_token = authorization_header.split(' ')[1]
            payload = jwt.decode(
                access_token, settings.SECRET_KEY, algorithms=['HS256']
            )

        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('access_token просрочен')
        except IndexError:
            raise exceptions.AuthenticationFailed('Префикс Token пропущен')

        user = User.objects.filter(id=payload['user_id']).first()
        if user is None:
            logger.info(f"User with id {payload['user_id']} is not found")
            raise exceptions.AuthenticationFailed('Пользователь не найден')

        if not user.get_is_active():
            logger.info(f"User {user.email} is not authorized")
            raise exceptions.AuthenticationFailed('Пользователь не активный')

        # self.enforce_csrf(request)
        user_logged_in.send(sender=user.__class__, request=request, user=user)
        logger.info(f"User {user.email} authorized successfully")
        return user, None

    def enforce_csrf(self, request):
        """
        Enforce CSRF validation
        """
        check = CSRFCheck()
        # populates request.META['CSRF_COOKIE'], which is used in process_view()
        check.process_request(request)
        reason = check.process_view(request, None, (), {})
        print(reason)
        if reason:
            # CSRF failed, bail with explicit error message
            # m = 'CSRF токен пропущен или не правильный.
            # Должен быть взят из cookies и быть передан по ключу X-CSRFToken'
            m = 'CSRF Failed: %s' % reason
            raise exceptions.PermissionDenied(m)
