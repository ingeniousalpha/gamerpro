import jwt
from django.http import Http404
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import (
    JWTAuthentication as BaseJWTAuthentication,
    AuthenticationFailed,
)

User = get_user_model()


class JWTAuthentication(BaseJWTAuthentication):
    @staticmethod
    def get_device_uuid_from_payload(validated_token):
        payload = jwt.decode(
            jwt=str(validated_token),
            key=settings.SECRET_KEY,
            algorithms=settings.SIMPLE_JWT['ALGORITHM']
        )

        if not payload.get("device_uuid"):
            raise AuthenticationFailed('Token should have device_uuid', code='bad_authorization_header')

        return payload["device_uuid"]

    @staticmethod
    def validate_device_uuid(user, payload_device_uuid):
        if str(user.device_uuid) != payload_device_uuid:
            raise AuthenticationFailed('Bad device uuid', code='user_not_found')

    @staticmethod
    def get_user_id_and_device_uuid_from_refresh(refresh: RefreshToken):
        try:
            return refresh.payload['user_id'], refresh.payload['device_uuid']
        except AttributeError as exc:
            raise AuthenticationFailed('Invalid refresh token', code='bad_authorization_header')

    @staticmethod
    def get_user_by_id(user_id):
        if User.objects.filter(id=user_id).exists():
            return User.objects.get(id=user_id)

        raise Http404

    @classmethod
    def validate_refresh_token(cls, refresh_token):
        refresh = RefreshToken(refresh_token)
        user_id, device_uuid = cls.get_user_id_and_device_uuid_from_refresh(refresh)
        cls.validate_device_uuid(
            cls.get_user_by_id(user_id), device_uuid
        )

    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        self.validate_device_uuid(user, self.get_device_uuid_from_payload(str(validated_token)))

        return user
