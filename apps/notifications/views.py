from rest_framework.generics import CreateAPIView, GenericAPIView, UpdateAPIView
from rest_framework.mixins import UpdateModelMixin
from rest_framework.response import Response

from apps.common.mixins import PublicJSONRendererMixin
from apps.notifications.models import FirebaseToken
from .serializers import FirebaseTokenSerializer


class SetUserFirebaseTokenView(PublicJSONRendererMixin, UpdateAPIView):
    queryset = FirebaseToken.objects.all()
    serializer_class = FirebaseTokenSerializer

    def get_object(self):
        return self.get_queryset().filter(token=self.request.data.get('token')).first()
