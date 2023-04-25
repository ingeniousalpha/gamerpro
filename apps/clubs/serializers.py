from rest_framework import serializers

from apps.clubs import ClubHallTypes
from apps.clubs.models import Club, ClubBranch, ClubComputer, ClubBranchPrice, ClubBranchProperty, ClubBranchHardware


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
        fields = ('number', 'is_booked')


class ClubBranchInfoSerializer(serializers.ModelSerializer):
    prices = serializers.SerializerMethodField()
    properties = serializers.SerializerMethodField()
    hardware = serializers.SerializerMethodField()
    computers = serializers.SerializerMethodField()

    class Meta:
        model = ClubBranch
        fields = (
            'prices',
            'properties',
            'hardware',
            'computers'
        )

    def get_prices(self, obj):
        queryset = obj.prices.all()
        if hall_type := self.context.get('hall_type'):
            queryset = queryset.filter(hall_type=hall_type)
        return ClubBranchPriceSerializer(queryset, many=True).data

    def get_properties(self, obj):
        queryset = obj.properties.all()
        if hall_type := self.context.get('hall_type'):
            queryset = queryset.filter(hall_type=hall_type)
        return ClubBranchPropertySerializer(queryset, many=True).data

    def get_hardware(self, obj):
        queryset = obj.hardware.all()
        if hall_type := self.context.get('hall_type'):
            queryset = queryset.filter(hall_type=hall_type)
        return ClubBranchHardwareSerializer(queryset, many=True).data

    def get_computers(self, obj):
        queryset = obj.computers.all()
        if hall_type := self.context.get('hall_type'):
            queryset = queryset.filter(hall_type=hall_type)
        return ClubComputerSerializer(queryset, many=True).data


class ClubBranchDetailSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    is_favorite = serializers.BooleanField(default=False)
    vip = serializers.SerializerMethodField()
    standard = serializers.SerializerMethodField()

    class Meta:
        model = ClubBranch
        fields = (
            'name',
            'address',
            'is_favorite',
            'vip',
            'standard',
        )

    def get_name(self, obj):
        return obj.club.name

    def get_vip(self, obj):
        return ClubBranchInfoSerializer(obj, context={"hall_type": ClubHallTypes.VIP}).data

    def get_standard(self, obj):
        return ClubBranchInfoSerializer(obj, context={"hall_type": ClubHallTypes.STANDARD}).data


class ClubBranchListSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    standard_total = serializers.SerializerMethodField()
    standard_booked = serializers.SerializerMethodField()
    vip_total = serializers.SerializerMethodField()
    vip_booked = serializers.SerializerMethodField()
    is_favorite = serializers.BooleanField(default=False)

    class Meta:
        model = ClubBranch
        fields = (
            'name',
            'description',
            'address',
            'standard_total',
            'standard_booked',
            'vip_total',
            'vip_booked',
            'is_favorite'
        )

    def get_name(self, obj):
        return obj.club.name

    def get_description(self, obj):
        return obj.club.description

    def get_standard_total(self, obj):
        return obj.computers.standard().count()

    def get_standard_booked(self, obj):
        return obj.computers.standard().filter(is_booked=True).count()

    def get_vip_total(self, obj):
        return obj.computers.vip().count()

    def get_vip_booked(self, obj):
        return obj.computers.vip().filter(is_booked=True).count()
