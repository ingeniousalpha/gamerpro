from django.conf import settings
from rest_framework.generics import CreateAPIView, UpdateAPIView

from apps.common.mixins import PublicJSONRendererMixin
from apps.notifications.models import FirebaseToken, JaryqLabOrder
from .exceptions import AccessDenied
from .serializers import FirebaseTokenSerializer, CreateJaryqLabOrderSerializer


class SetUserFirebaseTokenView(PublicJSONRendererMixin, UpdateAPIView):
    queryset = FirebaseToken.objects.all()
    serializer_class = FirebaseTokenSerializer

    def get_object(self):
        return self.get_queryset().filter(token=self.request.data.get('token')).first()


class CreateJaryqLabOrderView(PublicJSONRendererMixin, CreateAPIView):
    queryset = JaryqLabOrder.objects.all()
    serializer_class = CreateJaryqLabOrderSerializer

    def post(self, request, *args, **kwargs):
        api_key = request.headers.get('X-API-KEY')
        if not api_key or api_key != settings.JARYQLAB_API_KEY:
            raise AccessDenied
        return self.create(request, *args, **kwargs)
