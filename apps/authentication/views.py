from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenRefreshView as DRFTokenRefreshView
from rest_framework.generics import CreateAPIView, GenericAPIView

from apps.common.mixins import PublicJSONRendererMixin

# from apps.notifications.tasks import task_send_letter_for_email_confirmation
from .serializers import (
    SigninSerializer, TokenRefreshSerializer, LoginSerializer, VerifyOTPSerializer,
)
from ..notifications.services import send_otp

User = get_user_model()


class SigninView(PublicJSONRendererMixin, CreateAPIView):
    """ Регистрация/Вход в систему по номеру телефона """

    queryset = User.objects.all()
    serializer_class = SigninSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        mobile_phone = serializer.validated_data["mobile_phone"]
        serializer.save()
        send_otp(mobile_phone)
        return Response({}, status=status.HTTP_201_CREATED)



class VerifyOTPView(PublicJSONRendererMixin, GenericAPIView):
    serializer_class = VerifyOTPSerializer
    queryset = User.objects.all()

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(data=serializer.validated_data)


class TokenRefreshView(PublicJSONRendererMixin, DRFTokenRefreshView):
    serializer_class = TokenRefreshSerializer
