from rest_framework import serializers

from apps.clubs.models import ClubComputerGroup, ClubComputer, ClubBranchUser


class OuterComputerGroupsSaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClubComputerGroup
        fields = (
            'outer_id',
            'name',
            'club_branch',
        )


class OuterComputersSaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClubComputer
        fields = (
            'outer_id',
            'club_branch',
            'number',
            'group',
            'is_active_session',
            'is_locked',
            'is_broken',
            'outer_hostname',
        )


class OuterUserSaveSerializer(serializers.ModelSerializer):
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
