from rest_framework import routers

from apps.clubs.views import ClubViewSet


urlpatterns = []

router = routers.DefaultRouter()
router.register('', ClubViewSet)

urlpatterns += router.urls
