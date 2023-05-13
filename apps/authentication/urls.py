from django.urls import path
from .views import SigninView, TokenRefreshView, VerifyOTPView, SigninByUsernameView

urlpatterns = [
    path("signin/", SigninView.as_view(), name="signin_view"),
    path("signin/username", SigninByUsernameView.as_view(), name="signin_view"),
    path("verify-otp/", VerifyOTPView.as_view(), name="verify_otp_view"),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh_view"),
]
