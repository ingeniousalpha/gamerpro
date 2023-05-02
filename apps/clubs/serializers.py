from rest_framework import serializers

from apps.clubs import ClubHallTypes
from apps.clubs.models import Club, ClubBranch, ClubComputer, ClubBranchPrice, ClubBranchProperty, ClubBranchHardware, \
    ClubComputerGroup


class ClubListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Club
        fields = (
            'name',
            'description',
        )


class ClubBranchPriceSerializer(serializers.ModelSerializer):

    class Meta:
        model = ClubBranchPrice
        fields = ('name', 'price')


class ClubBranchPropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = ClubBranchProperty
        fields = ('name',)


class ClubBranchHardwareSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClubBranchHardware
        fields = ('name',)


class ClubComputerSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClubComputer
        fields = ('id', 'number', 'is_booked')


class ClubBranchInfoSerializer(serializers.ModelSerializer):
    hall_name = serializers.CharField(source='name')
    properties = serializers.SerializerMethodField()
    hardware = serializers.SerializerMethodField()
    prices = serializers.SerializerMethodField()
    computers = serializers.SerializerMethodField()

    class Meta:
        model = ClubComputerGroup
        fields = (
            'hall_name',
            'prices',
            'properties',
            'hardware',
            'computers'
        )

    def get_prices(self, obj):
        queryset = obj.club_branch.prices.filter(group_id=obj.id)
        return ClubBranchPriceSerializer(queryset, many=True).data

    def get_properties(self, obj):
        queryset = obj.club_branch.properties.filter(group_id=obj.id)
        return ClubBranchPropertySerializer(queryset, many=True).data

    def get_hardware(self, obj):
        queryset = obj.club_branch.hardware.filter(group_id=obj.id)
        return ClubBranchHardwareSerializer(queryset, many=True).data

    def get_computers(self, obj):
        queryset = obj.club_branch.computers.filter(group_id=obj.id)
        return ClubComputerSerializer(queryset, many=True).data


class ClubComputerListSerializer(serializers.ModelSerializer):
    hall_name = serializers.CharField(source='group.name')

    class Meta:
        model = ClubComputer
        fields = (
            'id',
            'number',
            'is_booked',
            'hall_name',
        )


class ClubBranchDetailSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    is_favorite = serializers.BooleanField(default=False)
    halls_info = ClubBranchInfoSerializer(source='computer_groups', many=True)
    computers = ClubComputerListSerializer(many=True)

    class Meta:
        model = ClubBranch
        fields = (
            'id',
            'name',
            'address',
            'is_favorite',
            'halls_info',
            'computers',
        )

    def get_name(self, obj):
        return obj.club.name

    # def get_vip(self, obj):
    #     return ClubBranchInfoSerializer(obj, context={"hall_type": ClubHallTypes.VIP}).data
    #
    # def get_standard(self, obj):
    #     return ClubBranchInfoSerializer(obj, context={"hall_type": ClubHallTypes.STANDARD}).data


class ClubComputerGroupLanding(serializers.ModelSerializer):
    hall_name = serializers.CharField(source='name')
    computers_total = serializers.SerializerMethodField()
    computers_free = serializers.SerializerMethodField()

    class Meta:
        model = ClubComputerGroup
        fields = (
            'hall_name',
            'computers_total',
            'computers_free',
        )

    def get_computers_total(self, obj):
        return obj.club_branch.computers.filter(group_id=obj.id).count()

    def get_computers_free(self, obj):
        return obj.club_branch.computers.filter(group_id=obj.id, is_booked=False).count()


class ClubBranchListSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    is_favorite = serializers.BooleanField(default=False)
    landing = ClubComputerGroupLanding(source='computer_groups', many=True)

    class Meta:
        model = ClubBranch
        fields = (
            'id',
            'name',
            'description',
            'address',
            'is_favorite',
            'landing',
        )

    def get_name(self, obj):
        return obj.club.name

    def get_description(self, obj):
        return obj.club.description
    #
    # def get_landing(self, obj):
    #     halls = []
    #     for group in obj.computer_groups.all():
    #         halls.append(ClubComputerGroupLanding(obj, context={"group_name": group.name}).data)
    #     return halls
