from django.urls import path
from .views import SigninView, TokenRefreshView, LoginView

urlpatterns = [
    path("signin/", SigninView.as_view(), name="signin_view"),
    path("verify-otp/", LoginView.as_view(), name="verify_otp_view"),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh_view"),
]