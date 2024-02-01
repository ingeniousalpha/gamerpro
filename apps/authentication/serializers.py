from django.contrib.auth import get_user_model
from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenRefreshSerializer as BaseTokenRefreshSerializer
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from six import text_type
import datetime

from .exceptions import UserNotFound
from .services import verify_otp, generate_access_and_refresh_tokens_for_user
from apps.users.services import get_or_create_user_by_phone
from apps.bot.tasks import bot_notify_about_new_user_task
from ..clubs.exceptions import ClubBranchNotFound, NeedToInputUserLogin, NeedToInputUserMobilePhone
from ..clubs.models import ClubBranch, ClubBranchUser
from ..common.exceptions import InvalidInputData
from ..integrations.gizmo.users_services import GizmoCreateUserService, GizmoGetUsersService
User = get_user_model()


class SigninByUsernameNewSerializer(serializers.ModelSerializer):
    club_branch = serializers.IntegerField(write_only=True)
    login = serializers.CharField(write_only=True)
    mobile_phone = serializers.CharField(write_only=True, required=False)
    first_name = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = (
            "club_branch",
            "login",
            "mobile_phone",
            "first_name",
        )

    def validate(self, attrs):
        attrs['club_branch'] = ClubBranch.objects.filter(id=attrs['club_branch']).first()
        if not attrs['club_branch']:
            raise ClubBranchNotFound

        GizmoGetUsersService(instance=attrs['club_branch']).run()

        club_user = ClubBranchUser.objects.filter(login=attrs['login'], club_branch=attrs['club_branch']).first()
        print(club_user)
        if not club_user and not attrs.get('mobile_phone'):
            raise NeedToInputUserMobilePhone
        elif not club_user and attrs.get('mobile_phone'):
            if attrs['club_branch'].club.name.lower() != "bro":
                gizmo_user_id = GizmoCreateUserService(instance=attrs['club_branch'], **attrs).run()
                attrs['gizmo_user_id'] = gizmo_user_id
        else:
            attrs['club_user'] = club_user
        return attrs

    def create(self, validated_data):
        if validated_data.get('club_user'):
            club_user = validated_data.get('club_user')
            if not club_user.user:
                user, _ = get_or_create_user_by_phone(validated_data['mobile_phone'])
                club_user.user = user
                club_user.save()
            else:
                user = club_user.user
        elif validated_data.get('gizmo_user_id') or validated_data['club_branch'].club.name.lower() == "bro":
            user, _ = get_or_create_user_by_phone(validated_data['mobile_phone'])
            ClubBranchUser.objects.create(
                club_branch=validated_data['club_branch'],
                gizmo_id=validated_data.get('gizmo_user_id'),
                gizmo_phone=validated_data['mobile_phone'],
                login=validated_data['login'],
                first_name=validated_data['first_name'],
                user=user,
            )
            if validated_data['club_branch'].club.name.lower() == "bro":
                bot_notify_about_new_user_task.delay(
                    club_branch_id=validated_data['club_branch'].id,
                    login=validated_data['login'],
                    first_name=validated_data['first_name'],
                )
        return user

    def to_representation(self, instance):
        return generate_access_and_refresh_tokens_for_user(instance)


class SigninWithoutOTPSerializer(serializers.ModelSerializer):
    club_branch = serializers.IntegerField(write_only=True)
    login = serializers.CharField(write_only=True, required=False)
    first_name = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = (
            "mobile_phone",
            "login",
            "club_branch",
            "first_name",
        )
        extra_kwargs = {
            "mobile_phone": {"write_only": True}
        }

    def validate(self, attrs):
        attrs['club_branch'] = ClubBranch.objects.filter(id=attrs['club_branch']).first()
        if not attrs['club_branch']:
            raise ClubBranchNotFound

        GizmoGetUsersService(instance=attrs['club_branch']).run()

        club_user = ClubBranchUser.objects.filter(gizmo_phone=attrs['mobile_phone'], club_branch=attrs['club_branch']).first()
        print(club_user)
        if not club_user and not attrs.get('login'):
            raise NeedToInputUserLogin
        elif not club_user and attrs.get('login'):
            if attrs['club_branch'].club.name.lower() != "bro":
                gizmo_user_id = GizmoCreateUserService(instance=attrs['club_branch'], **attrs).run()
                attrs['gizmo_user_id'] = gizmo_user_id
        else:
            attrs['club_user'] = club_user
        return attrs

    def create(self, validated_data):
        user, _ = get_or_create_user_by_phone(validated_data['mobile_phone'])
        if validated_data.get('club_user'):
            club_user = validated_data.get('club_user')
            if not club_user.user:
                club_user.user = user
                club_user.save()
        elif validated_data.get('gizmo_user_id') or validated_data['club_branch'].club.name.lower() == "bro":
            ClubBranchUser.objects.create(
                club_branch=validated_data['club_branch'],
                gizmo_id=validated_data.get('gizmo_user_id'),
                gizmo_phone=validated_data['mobile_phone'],
                login=validated_data['login'],
                first_name=validated_data['first_name'],
                user=user,
            )
            if validated_data['club_branch'].club.name.lower() == "bro":
                bot_notify_about_new_user_task.delay(
                    club_branch_id=validated_data['club_branch'].id,
                    login=validated_data['login'],
                    first_name=validated_data['first_name'],
                )
        return user

    def to_representation(self, instance):
        return generate_access_and_refresh_tokens_for_user(instance)


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


CUSTOM_LIFETIME = datetime.timedelta(seconds=30)


class MyTokenObtainSerializer(serializers.Serializer):
    mobile_phone = serializers.CharField()

    def validate(self, attrs):
        user = User.objects.filter(mobile_phone=attrs['mobile_phone']).first()
        if not user:
            raise UserNotFound

        refresh = TokenObtainPairSerializer.get_token(user)
        new_token = refresh.access_token
        new_token.set_exp(lifetime=CUSTOM_LIFETIME)
        return {
            "refresh_token": text_type(refresh),
            "access_token": text_type(new_token),
        }

