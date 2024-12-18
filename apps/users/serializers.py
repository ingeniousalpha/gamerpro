from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class ProfileSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    mobile_phone = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ("id", "mobile_phone", "name", "email")
