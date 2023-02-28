import logging

from django.shortcuts import render
from rest_framework import status
from rest_framework.parsers import MultiPartParser, JSONParser
from rest_framework.response import Response
from rest_framework.generics import RetrieveUpdateAPIView, GenericAPIView, ListAPIView, ListCreateAPIView

from apps.common.encryption import decrypt
from apps.common.exceptions import EmailConfirmationExpired, EmailAlreadyConfirmed
from apps.common.mixins import JSONRendererMixin, PublicJSONRendererMixin
from apps.common.services import generate_password
from apps.users.serializers import UserProfileSerializer
from apps.users.services import get_user

logger = logging.getLogger('users')


class AccountView(JSONRendererMixin, RetrieveUpdateAPIView):
    """ Получить/редактировать инфо о пользователе """

    parser_classes = (JSONParser, MultiPartParser)

    def get_serializer_class(self):
        if hasattr(self.request, 'method'):
            if self.request.method == 'GET':
                return UserProfileSerializer
            # if self.request.method == 'PUT':
            #     return UserUpdateSerializer

    def retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(instance=request.user)
        return Response(serializer.data)

    # def update(self, request, *args, **kwargs):
    #     serializer = self.get_serializer(
    #         instance=request.user,
    #         data=request.data,
    #         partial=True
    #     )
    #     serializer.is_valid(raise_exception=True)
    #     serializer.save()
    #
    #     return Response(serializer.validated_data)


# class PasswordResetView(JSONRendererMixin, GenericAPIView):
#     serializer_class = PasswordResetSerializer
#
#     def post(self, request):
#         serializer = self.get_serializer(instance=request.user, data=request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response(serializer.data, status.HTTP_200_OK)


# class PasswordRecoveryView(PublicJSONRendererMixin, GenericAPIView):
#     def post(self, request):
#         email = request.data.get('email')
#         user = get_user(email)
#
#         if user:
#             new_password = generate_password()
#             user.set_password(new_password)
#             user.save(update_fields=['password'])
#             task_send_letter_for_password_recovery.delay(email, new_password, request.language)
#
#         return Response(data={}, status=status.HTTP_200_OK)


# class EmailConfirmationView(PublicJSONRendererMixin, GenericAPIView):
#
#     def get(self, request, encrypted_email):
#         email = decrypt(encrypted_email, with_timestamp=True)
#         user = get_user(email)
#         expired_msg = False
#
#         if user:
#             user.set_active()
#             logger.info(f"User {email} email confirmation succeed")
#         else:
#             expired_msg = EmailConfirmationExpired.get_message(request.language)
#
#         # print(settings.TEMPLATE_DIR)
#         return render(
#             request, "users/email_confirmation.html",
#             {"expired_msg": expired_msg}
#         )
#
#     def post(self, request):
#         email = decrypt(request.data.get('encrypted_email'), with_timestamp=True)
#         user = get_user(email)
#
#         if user:
#             if not user.is_email_confirmed:
#                 user.set_active()
#                 logger.info(f"User {email} email confirmation succeed")
#             else:
#                 raise EmailAlreadyConfirmed
#         else:
#             raise EmailConfirmationExpired
#
#         return Response({}, 200)
