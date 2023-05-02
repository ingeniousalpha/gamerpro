from rest_framework import serializers

from apps.clubs.models import ClubBranchUser, ClubComputer, ClubComputerGroup


class GizmoUsersSaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClubBranchUser
        fields = (
            'gizmo_id',
            'login',
            'club_branch',
        )


class GizmoComputersSaveSerializer(serializers.ModelSerializer):
    group = serializers.IntegerField(source='group.gizmo_id')

    class Meta:
        model = ClubComputer
        fields = (
            'gizmo_id',
            'gizmo_hostname',
            'is_booked',
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
