from rest_framework import serializers

from apps.clubs.models import ClubBranchUser, ClubComputer, ClubComputerGroup, ClubTimePacketGroup, ClubTimePacket


class GizmoTimePacketGroupSaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClubTimePacketGroup
        fields = (
            'gizmo_id',
            'name',
            'club_branch'
        )


class GizmoTimePacketSaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClubTimePacket
        fields = '__all__'

    def create(self, validated_data):
        display_name = validated_data.pop('display_name', "")
        time_packet, _ = self.Meta.model.objects.get_or_create(**validated_data)
        if not time_packet.display_name:
            time_packet.display_name = display_name
            time_packet.save(update_fields=['display_name'])
        return time_packet
