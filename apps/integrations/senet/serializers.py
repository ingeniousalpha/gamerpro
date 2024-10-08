from rest_framework import serializers

from apps.clubs.models import ClubTimePacket


class SenetTimePacketCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClubTimePacket
        fields = '__all__'
