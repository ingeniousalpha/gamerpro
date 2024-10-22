from rest_framework import serializers

from apps.clubs.models import ClubTimePacket


class SenetTimePacketCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClubTimePacket
        fields = (
            "outer_id",
            "outer_name",
            "display_name",
            "price",
            "club"
        )
