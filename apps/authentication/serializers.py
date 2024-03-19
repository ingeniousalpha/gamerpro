from django.contrib.auth import get_user_model
from django.conf import settings
from django.db.models import Q
from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenRefreshSerializer as BaseTokenRefreshSerializer
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from six import text_type
import datetime

from .exceptions import UserNotFound, InvalidOTP
from .models import TGAuthUser, VerifiedOTP
from .services import verify_otp, generate_access_and_refresh_tokens_for_user, tg_auth_verify, tg_auth_send_otp_code
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
            # Create user in Gizmo
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
                first_name=validated_data.get('first_name'),
                user=user,
            )
            if validated_data['club_branch'].club.name.lower() == "bro":
                bot_notify_about_new_user_task.delay(
                    club_branch_id=validated_data['club_branch'].id,
                    login=validated_data['login'],
                    first_name=validated_data.get('first_name'),
                )
        return user

    def to_representation(self, instance):
        return generate_access_and_refresh_tokens_for_user(instance)


class OLDSigninWithOTPSerializer(serializers.ModelSerializer):
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
        else:
            attrs['club_user'] = club_user
        return attrs

    def create(self, validated_data):
        user, _ = get_or_create_user_by_phone(validated_data['mobile_phone'])
        club_user = validated_data.get('club_user')
        if not club_user:
            ClubBranchUser.objects.create(
                club_branch=validated_data['club_branch'],
                gizmo_phone=validated_data['mobile_phone'],
                first_name=validated_data.get('first_name'),
                login=validated_data['login'],
                user=user,
            )
        elif not club_user.user:
            club_user.user = user
            club_user.save(update_fields=['user'])
        return user

    def to_representation(self, instance):
        # when there is tg_user - send code
        # when there is not tg_user - send tg url
        tg_user = TGAuthUser.objects.filter(mobile_phone=instance.mobile_phone).first()
        if not tg_user:
            return {"telegram_auth_url": f"https://t.me/{settings.TG_AUTH_BOT_USERNAME}"}
        result = tg_auth_send_otp_code(str(instance.mobile_phone))
        if result:
            return {}
        raise InvalidInputData


class SigninWithOTPSerializer(serializers.Serializer):
    mobile_phone = serializers.CharField(write_only=True)
    club_branch = serializers.IntegerField(write_only=True)

    def validate(self, attrs):
        attrs['club_branch'] = ClubBranch.objects.filter(id=attrs['club_branch']).first()
        if not attrs['club_branch']:
            raise ClubBranchNotFound
        # when there is tg_user - send code
        # when there is not tg_user - send tg url
        tg_user = TGAuthUser.objects.filter(mobile_phone=str(attrs['mobile_phone'])).first()
        if not tg_user:
            return {"telegram_auth_url": f"https://t.me/{settings.TG_AUTH_BOT_USERNAME}"}
        result = tg_auth_send_otp_code(str(attrs['mobile_phone']))
        if result:
            return {}
        raise InvalidInputData


class VerifyOTPSerializer(serializers.Serializer):
    club_branch = serializers.IntegerField(write_only=True)
    mobile_phone = serializers.CharField(required=True, write_only=True)
    otp_code = serializers.CharField(required=True, write_only=True, min_length=4, max_length=4)

    def validate_otp_code(self, value):
        if not value.isnumeric():
            raise InvalidInputData
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        print(attrs)
        club_branch = ClubBranch.objects.filter(id=attrs.pop('club_branch')).first()
        if not club_branch:
            raise ClubBranchNotFound

        if not tg_auth_verify(**attrs):
            raise InvalidOTP

        VerifiedOTP.objects.create(
            mobile_phone=attrs['mobile_phone'],
            otp_code=attrs['otp_code']
        )

        user, _ = get_or_create_user_by_phone(attrs['mobile_phone'])

        GizmoGetUsersService(instance=club_branch).run()
        club_user = ClubBranchUser.objects.filter(
            gizmo_phone=attrs['mobile_phone'],
            club_branch=club_branch
        ).first()

        if not club_user or not club_user.is_verified:
            raise NeedToInputUserLogin
        elif not club_user.user:
            club_user.user = user
            club_user.save(update_fields=['user'])

        # if not club_user.is_verified:
        #     if club_branch.club.name.lower() == "bro":
        #         bot_notify_about_new_user_task.delay(
        #             club_branch_id=club_branch.id,
        #             login=club_user.login,
        #             first_name=club_user.first_name,
        #         )
        #     else:
        #         gizmo_user_id = GizmoCreateUserService(
        #             instance=club_branch,
        #             login=club_user.login,
        #             first_name=club_user.first_name,
        #             mobile_phone=club_user.gizmo_phone
        #         ).run()
        #         club_user.gizmo_id = gizmo_user_id
        #         club_user.save(update_fields=['gizmo_id'])
        #     user.is_mobile_phone_verified = True
        #     user.save(update_fields=['is_mobile_phone_verified'])

        return generate_access_and_refresh_tokens_for_user(user)


class RegisterV2Serializer(serializers.ModelSerializer):
    club_branch = serializers.IntegerField(write_only=True)
    login = serializers.CharField(write_only=True, required=True)
    first_name = serializers.CharField(write_only=True, required=False)
    otp_code = serializers.CharField(required=True, write_only=True, min_length=4, max_length=4)

    class Meta:
        model = User
        fields = (
            "mobile_phone",
            "login",
            "club_branch",
            "first_name",
            "otp_code",
        )
        extra_kwargs = {
            "mobile_phone": {"write_only": True}
        }

    def validate(self, attrs):
        attrs['club_branch'] = ClubBranch.objects.filter(id=attrs['club_branch']).first()
        if not attrs['club_branch']:
            raise ClubBranchNotFound

        if not VerifiedOTP.objects.filter(
                otp_code=attrs['otp_code'],
                mobile_phone=attrs['mobile_phone']
        ).exists():
            raise InvalidOTP

        return attrs

    def create(self, validated_data):
        user, _ = get_or_create_user_by_phone(validated_data['mobile_phone'])
        club_user = ClubBranchUser.objects.filter(
            Q(club_branch=validated_data['club_branch']) & (
                    Q(gizmo_phone=validated_data['mobile_phone']) | Q(login=validated_data['login'])
            )
        ).first()
        if not club_user:
            club_user = ClubBranchUser.objects.create(
                gizmo_phone=validated_data['mobile_phone'],
                club_branch=validated_data['club_branch'],
                login=validated_data['login'],
                first_name=validated_data.get('first_name'),
                gizmo_id=None,
                user=user,
            )
        else:
            if not club_user.gizmo_phone:
                club_user.gizmo_phone = validated_data['mobile_phone']
                club_user.save(update_fields=['gizmo_phone'])
            if club_user.is_verified:
                return user

        if validated_data['club_branch'].club.name.lower() == "bro":
            bot_notify_about_new_user_task.delay(
                club_branch_id=validated_data['club_branch'].id,
                login=validated_data['login'],
                first_name=validated_data.get('first_name'),
            )
        else:
            gizmo_user_id = GizmoCreateUserService(
                instance=validated_data['club_branch'],
                login=validated_data["login"],
                first_name=validated_data["first_name"],
                mobile_phone=validated_data["mobile_phone"],
            ).run()
            club_user.gizmo_id = gizmo_user_id
            club_user.save(update_fields=['gizmo_id'])
        return user

    def to_representation(self, instance):
        return generate_access_and_refresh_tokens_for_user(instance)


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

