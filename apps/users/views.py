from rest_framework.generics import RetrieveUpdateAPIView

from apps.common.mixins import PrivateJSONRendererMixin
from apps.users.serializers import ProfileSerializer


class ProfileView(PrivateJSONRendererMixin, RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer

    def get_object(self):
        return self.request.user
