from rest_framework import serializers

from apps.common.serializers import RequestUserPropertyMixin
from apps.notifications.models import FirebaseToken


class FirebaseTokenSerializer(RequestUserPropertyMixin, serializers.ModelSerializer):
    class Meta:
        model = FirebaseToken
        fields = (
            'token',
        )

    def validate(self, attrs):
        if self.user:
            attrs['user'] = self.user
        return attrs
