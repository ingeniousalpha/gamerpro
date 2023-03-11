from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer as BaseTokenObtainPairSerializer
from rest_framework_simplejwt.serializers import TokenRefreshSerializer as BaseTokenRefreshSerializer

from .exceptions import UserAlreadyExists
from .services import validate_password
from apps.users.services import create_user, get_user_by_login

User = get_user_model()


class UserCredentials(serializers.Serializer):
    email = serializers.EmailField(required=True, write_only=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate_password(self, value):
        validate_password(value)
        return value

    def to_representation(self, instance):
        refresh = CustomTokenObtainPairSerializer.get_token(instance)

        return {
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
        }


class RegisterSerializer(UserCredentials, serializers.ModelSerializer):

    class Meta:
        model = User
        fields = "mobile_phone",

    def validate_email(self, value):
        if User.objects.filter(email=value, is_email_confirmed=True).exists():
            raise UserAlreadyExists
        return value

    def create(self, validated_data):
        user = create_user(validated_data['email'], validated_data['password'])
        return user


class LoginSerializer(UserCredentials):

    def validate(self, attrs):
        self.instance = get_user_by_login(attrs['email'], attrs['password'], raise_exception=True)
        return attrs


class CustomTokenObtainPairSerializer(BaseTokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # token["device_uuid"] = str(user.device_uuid)

        return token


class TokenObtainPairSerializer(serializers.Serializer): # noqa
    def validate(self, attrs):
        user = self.context["user"]
        refresh = CustomTokenObtainPairSerializer.get_token(user)

        return {
            "refresh_token": str(refresh),
            "access_token": str(refresh.access_token),
        }


class TokenRefreshSerializer(BaseTokenRefreshSerializer):
    def validate(self, attrs):
        # JWTAuthentication.validate_refresh_token(attrs['refresh'])
        data = super().validate(attrs)
        return {
            "access_token": data['access'],
            "refresh_token": data['refresh'],
        }
