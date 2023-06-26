from django.contrib.auth import get_user_model
from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenRefreshSerializer as BaseTokenRefreshSerializer

from .services import verify_otp, generate_access_and_refresh_tokens_for_user
from apps.users.services import get_or_create_user_by_phone
from ..clubs.exceptions import ClubBranchNotFound
from ..clubs.models import ClubBranch
from ..common.exceptions import InvalidInputData

User = get_user_model()


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
        return generate_access_and_refresh_tokens_for_user(user)


class SigninByUsernameSerializer(serializers.Serializer):
    username = serializers.CharField()
    club_branch = serializers.IntegerField()

    def validate_club_branch(self, value):
        club_branch = ClubBranch.objects.filter(pk=value).first()
        if not club_branch:
            raise ClubBranchNotFound
        self.context['club_branch'] = club_branch
        return value


class TokenRefreshSerializer(BaseTokenRefreshSerializer):
    def validate(self, attrs):
        # JWTAuthentication.validate_refresh_token(attrs['refresh'])
        data = super().validate(attrs)
        return {
            "access_token": data['access'],
            "refresh_token": data['refresh'],
        }
