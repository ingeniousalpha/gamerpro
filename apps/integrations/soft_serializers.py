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
            'number',
            'outer_hostname',
            'is_locked',
            'club_branch',
            'group',
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
