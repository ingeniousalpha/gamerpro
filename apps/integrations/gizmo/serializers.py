from rest_framework import serializers

from apps.clubs.models import ClubBranchUser, ClubComputer, ClubComputerGroup, ClubTimePacketGroup, ClubTimePacket


class GizmoUserSaveSerializer(serializers.ModelSerializer):
    outer_phone = serializers.CharField(required=False, allow_blank=True)
    login = serializers.CharField(required=False, allow_blank=True)
    first_name = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = ClubBranchUser
        fields = (
            'outer_id',
            'outer_phone',
            'login',
            'first_name',
            'club_branch',
        )


class GizmoComputersSaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClubComputer
        fields = (
            'outer_id',
            'number',
            'gizmo_hostname',
            'is_locked',
            'is_deleted',
            'club_branch',
            'group',
        )


class GizmoTimePacketGroupSaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClubTimePacketGroup
        fields = (
            'outer_id',
            'name',
            'club_branch'
        )


class GizmoTimePacketSaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClubTimePacket
        fields = (
            "outer_id",
            "outer_name",
            "display_name",
            "description",
            "price",
            "minutes",
            "packet_group",
            "club_computer_group"
        )

    def create(self, validated_data):
        display_name = validated_data.pop('display_name', "")
        print(validated_data)
        time_packet, _ = self.Meta.model.objects.get_or_create(**validated_data)
        if not time_packet.display_name:
            time_packet.display_name = display_name
            time_packet.save(update_fields=['display_name'])
        return time_packet
