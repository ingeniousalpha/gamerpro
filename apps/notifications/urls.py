from django.urls import path

from .views import SetUserFirebaseTokenView


urlpatterns = [
    path('setup', SetUserFirebaseTokenView.as_view())
]