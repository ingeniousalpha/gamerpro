from django.contrib.auth import get_user_model
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenRefreshView as DRFTokenRefreshView
from rest_framework.generics import CreateAPIView, GenericAPIView

from apps.common.mixins import PublicJSONRendererMixin

# from apps.notifications.tasks import task_send_letter_for_email_confirmation
from .serializers import (
    RegisterSerializer, TokenRefreshSerializer, LoginSerializer,
)

User = get_user_model()


class SigninView(PublicJSONRendererMixin, CreateAPIView):
    """ Регистрация в системе """

    queryset = User.objects.all()
    serializer_class = RegisterSerializer

    def perform_create(self, serializer):
        email = serializer.validated_data["email"]
        serializer.save()
        # task_send_letter_for_email_confirmation.delay(email, self.request.language)


class TokenRefreshView(PublicJSONRendererMixin, DRFTokenRefreshView):
    serializer_class = TokenRefreshSerializer


class LoginView(PublicJSONRendererMixin, GenericAPIView):
    serializer_class = LoginSerializer
    queryset = User.objects.all()

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(data=serializer.data)


# @api_view(['POST'])
# @permission_classes([AllowAny, ])
# # @ensure_csrf_cookie
# @base_view
# def authenticate_user(request):  # LOG IN ENDPOINT
#     """ Логин пользователя"""
#
#     resp_body = response_body()
#     language = get_language(request)
#
#     data = request.data
#     given, msg = credentials_given(data)
#     if not given:
#         resp_status = status.HTTP_417_EXPECTATION_FAILED
#         resp_body['error'] = msg
#         return Response(resp_body, status=resp_status)
#
#     email = request.data['email'].lower()
#     password = request.data['password']
#     logger.info(f"User {email} log in started")
#
#     # logger.debug("Email encryption: ")
#     # encrypted_email = encrypt(email)
#     # logger.debug(encrypted_email)
#     # logger.debug(type(encrypted_email))
#     # decrypted_email = decrypt(encrypted_email)
#     # logger.debug(decrypted_email)
#
#     exists, msg = user_exists(email=email, password=password, lang=language)
#     if exists:
#         # if not user.check_password(password):
#         #     resp_body['error'] = 'Given wrong password'
#         #     return Response(resp_body)
#         user = User.objects.get(email=email)
#         if "firebase_token" in request.data:
#             user.firebase_token = request.data["firebase_token"]
#             subscribe_to_language_topic(user.language, user.firebase_token)
#             user.save()
#         logger.debug(f"user.password: {user.password}")
#         logger.debug(user.check_password(user.password))
#         logger.debug(f"user._password: {user._password}")
#
#         if 'Accept-Language' in request.headers:
#             user.language = request.headers['Accept-Language']
#             user.save()
#
#         expired_msg = subs_expired(user, language)
#         if expired_msg:
#             resp_body['error'] = expired_msg
#
#         try:
#             logger.info(user)
#             UserSerializer = get_serializer_class_by_language("User", lang=language)
#             logger.info(UserSerializer)
#             context = {"request": request}
#             serialized_user = UserSerializer(user, context=context).data
#             logger.info(serialized_user)
#
#             access_token = generate_access_token(user)
#             logger.info("it is access token: ")
#             logger.info(access_token)
#             # refresh_token = generate_refresh_token(user)
#             # print("it is refresh token: ")
#             # print(refresh_token)
#
#             resp_body["data"] = {
#                 'access_token': access_token,
#                 # 'refresh_token': refresh_token,
#                 'user': serialized_user,
#             }
#             user_logged_in.send(sender=user.__class__, request=request, user=user)
#             logger.info(f"User {email} log in succeed")
#             response = Response(resp_body, status=status.HTTP_200_OK)
#             # response.set_cookie(key='refresh_token', value=refresh_token, httponly=True)
#             return response
#
#         except Exception as e:
#             resp_body['error'] = e
#             logger.info(f"User {email} log in failed: {str(e)}")
#             return Response(resp_body)
#     else:
#         resp_body['error'] = msg
#         logger.info(f"User {email} log in failed: {msg}")
#         return Response(resp_body, status=status.HTTP_403_FORBIDDEN)

