from django.urls import path
from .views import (
    AccountView,
)
urlpatterns = [
    path('profile/', AccountView.as_view()),
    # path('email-confirmation/<str:encrypted_email>/', EmailConfirmationView.as_view(), name='email_confirmation_get_view'),
    # path('email-confirmation/', EmailConfirmationView.as_view(), name='email_confirmation_post_view'),
    # path('password-reset/', PasswordResetView.as_view(), name='password_reset_view'),
    # path('password-recovery/', PasswordRecoveryView.as_view(), name='password_recovery_view'),
    # path('password_recovery/<str:encrypted>/', password_recovery_view, name='password_recovery_view'),
]
