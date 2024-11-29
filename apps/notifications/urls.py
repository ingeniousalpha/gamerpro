from django.urls import path

from .views import SetUserFirebaseTokenView, CreateJaryqLabOrderView

urlpatterns = [
    path('setup', SetUserFirebaseTokenView.as_view()),
    path('jaryqlab', CreateJaryqLabOrderView.as_view()),
]
