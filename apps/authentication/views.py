import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.generics import CreateAPIView, GenericAPIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView as DRFTokenRefreshView

from apps.common.mixins import PublicJSONRendererMixin
from .models import TGAuthUser
from .serializers import (
    SigninWithoutOTPSerializer, TokenRefreshSerializer, VerifyOTPSerializer,
    MyTokenObtainSerializer, SigninByUsernameNewSerializer,
    SigninWithOTPSerializer, RegisterV2Serializer, VerifyOTPV3Serializer
)
from .services import tg_auth_send_otp_code, generate_access_and_refresh_tokens_for_user
from ..common.exceptions import InvalidInputData

User = get_user_model()
logger = logging.getLogger("authentication")


class SigninView(PublicJSONRendererMixin, CreateAPIView):
    """ Регистрация/Вход в систему по номеру телефона """

    queryset = User.objects.all()
    serializer_class = SigninWithoutOTPSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        # mobile_phone = serializer.validated_data["mobile_phone"]
        # send_otp(mobile_phone)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SigninV2View(PublicJSONRendererMixin, CreateAPIView):
    """ Регистрация/Вход в систему по номеру телефона c OTP"""

    queryset = User.objects.all()
    serializer_class = SigninWithOTPSerializer

    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class VerifyOTPV2View(PublicJSONRendererMixin, GenericAPIView):
    queryset = User.objects.all()
    serializer_class = VerifyOTPSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(data=serializer.validated_data)


class RegisterV2View(PublicJSONRendererMixin, GenericAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterV2Serializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data=serializer.data)


class SigninByUsernameView(PublicJSONRendererMixin, GenericAPIView):
    serializer_class = SigninByUsernameNewSerializer
    queryset = User.objects.all()

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        # club_user = get_club_branch_user_by_username(serializer.data['username'])
        #
        # if not club_user:
        #     club_user = GizmoGetUserByUsernameService(
        #         instance=serializer.context['club_branch'], username=serializer.data['username']
        #     ).run()
        # check_user_session(club_user)

        return Response(serializer.data)


class TokenRefreshView(PublicJSONRendererMixin, DRFTokenRefreshView):
    serializer_class = TokenRefreshSerializer


class MyFastTokenView(TokenObtainPairView):
    serializer_class = MyTokenObtainSerializer


class SendOTPV3View(PublicJSONRendererMixin, GenericAPIView):
    queryset = TGAuthUser.objects.all()
    serializer_class = None

    def post(self, request, *args, **kwargs):
        mobile_phone = request.data.get('mobile_phone')
        tg_user = self.get_queryset().filter(mobile_phone=mobile_phone).first()
        if tg_user:
            if not tg_auth_send_otp_code(mobile_phone):
                raise InvalidInputData
            data = {}
        else:
            data = {"telegram_auth_url": f"https://t.me/{settings.TG_AUTH_BOT_USERNAME}"}
        return Response(data)


class VerifyOTPV3View(PublicJSONRendererMixin, GenericAPIView):
    queryset = User.objects.all()
    serializer_class = VerifyOTPV3Serializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user, created = User.objects.update_or_create(
            mobile_phone=request.data.get('mobile_phone'),
            defaults={'last_otp': request.data.get('otp_code'), 'is_mobile_phone_verified': True}
        )
        if user.email and user.email[-7:] == '@gp.com':
            user.email = None
            user.save(update_fields=['email', 'updated_at'])
        return Response(generate_access_and_refresh_tokens_for_user(user))
