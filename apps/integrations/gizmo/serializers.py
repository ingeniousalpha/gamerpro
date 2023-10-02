from rest_framework import serializers

from apps.clubs.models import ClubBranchUser, ClubComputer, ClubComputerGroup, ClubTimePacketGroup, ClubTimePacket


class GizmoUserSaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClubBranchUser
        fields = (
            'gizmo_id',
            'gizmo_phone',
            'login',
            'club_branch',
        )


class GizmoComputersSaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClubComputer
        fields = (
            'gizmo_id',
            'number',
            'gizmo_hostname',
            'is_locked',
            'club_branch',
            'group',
        )


class GizmoComputerGroupsSaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClubComputerGroup
        fields = (
            'gizmo_id',
            'name',
            'club_branch',
        )


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
