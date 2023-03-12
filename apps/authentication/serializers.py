from django.contrib.auth import get_user_model
from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer as BaseTokenObtainPairSerializer
from rest_framework_simplejwt.serializers import TokenRefreshSerializer as BaseTokenRefreshSerializer

from .services import validate_password, verify_otp
from apps.users.services import get_user_by_login, get_or_create_user_by_phone
from ..common.exceptions import InvalidInputData

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


class SigninSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = "mobile_phone",

    def create(self, validated_data):
        user, _ = get_or_create_user_by_phone(validated_data['mobile_phone'])
        return user


class VerifyOTPSerializer(serializers.Serializer):
    mobile_phone = PhoneNumberField(required=True, write_only=True)
    otp_code = serializers.CharField(required=True, write_only=True, min_length=4, max_length=4)

    def validate_otp_code(self, value):
        if not value.isnumeric():
            raise InvalidInputData
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        print(attrs)
        verify_otp(code=attrs['otp_code'], mobile_phone=attrs['mobile_phone'], save=True)

        user, _ = get_or_create_user_by_phone(attrs['mobile_phone'])
        refresh = CustomTokenObtainPairSerializer.get_token(user)
        return {
            "refresh_token": str(refresh),
            "access_token": str(refresh.access_token),
        }
        # return attrs


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
