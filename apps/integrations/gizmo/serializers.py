from rest_framework import serializers

from apps.clubs.models import ClubBranchUser, ClubComputer, ClubComputerGroup


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
