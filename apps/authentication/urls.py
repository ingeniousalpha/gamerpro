from django.urls import path
from .views import RegisterView, TokenRefreshView, LoginView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register_view"),
    path("login/", LoginView.as_view(), name="login_view"),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh_view"),
]
