from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenRefreshView as DRFTokenRefreshView
from rest_framework.generics import CreateAPIView, GenericAPIView


from apps.common.mixins import PublicJSONRendererMixin

# from apps.notifications.tasks import task_send_letter_for_email_confirmation
from .serializers import (
    SigninWithoutOTPSerializer, TokenRefreshSerializer, SigninByUsernameSerializer, VerifyOTPSerializer,
    MyTokenObtainSerializer, SigninByUsernameNewSerializer,
)
from .services import generate_access_and_refresh_tokens_for_user
from ..bookings.services import check_user_session
from ..clubs.services import get_club_branch_user_by_username
from ..integrations.gizmo.users_services import GizmoGetUserByUsernameService
from ..users.services import get_or_create_user_by_phone

from rest_framework_simplejwt.views import TokenObtainPairView


User = get_user_model()


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


class VerifyOTPView(PublicJSONRendererMixin, GenericAPIView):
    serializer_class = VerifyOTPSerializer
    queryset = User.objects.all()

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(data=serializer.validated_data)


class TokenRefreshView(PublicJSONRendererMixin, DRFTokenRefreshView):
    serializer_class = TokenRefreshSerializer


class MyFastTokenView(TokenObtainPairView):
    serializer_class = MyTokenObtainSerializer
