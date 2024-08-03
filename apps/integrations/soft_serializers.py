from rest_framework import serializers

from apps.clubs.models import ClubComputerGroup


class OuterComputerGroupsSaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClubComputerGroup
        fields = (
            'outer_id',
            'name',
            'club_branch',
        )
