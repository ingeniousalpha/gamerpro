from django.urls import path
from .views import (
    SigninView,
    SigninV2View,
    TokenRefreshView,
    VerifyOTPV2View,
    SigninByUsernameView,
    MyFastTokenView,
)

urlpatterns = [
    path("signin/", SigninView.as_view(), name="signin_view"),
    path("signin/fast_token", MyFastTokenView.as_view(), name="fast_token_view"),
    path("signin/username", SigninByUsernameView.as_view(), name="signin_view"),
    # path("signin/bro", SigninBroView.as_view(), name="signin_bro_view"),
    path("v2/signin/", SigninV2View.as_view(), name="signin_view"),
    path("v2/verify/", VerifyOTPV2View.as_view(), name="verify_otp_view"),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh_view"),
]


