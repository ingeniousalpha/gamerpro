from django.core.cache import cache
from django.db.models import Subquery, OuterRef
from django.utils import timezone
from rest_framework import serializers

from apps.authentication.exceptions import UserNotFound
from apps.bookings.models import BookedComputer
from apps.clubs import ClubHallTypes
from apps.clubs.models import Club, ClubBranch, ClubComputer, ClubBranchPrice, ClubBranchProperty, ClubBranchHardware, \
    ClubComputerGroup, ClubBranchUser, ClubTimePacket
from apps.common.serializers import RequestUserPropertyMixin
from apps.integrations.gizmo.users_services import GizmoGetUserBalanceService


class BaseClubUserSerializer(RequestUserPropertyMixin, serializers.Serializer):
    login = serializers.SerializerMethodField()
    balance = serializers.SerializerMethodField()
    is_verified = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'login',
            'balance',
            'is_verified',
        )

    def get_balance(self, obj):
        if self.user:
            club_user = ClubBranchUser.objects.filter(user=self.user, club_branch=obj).first()
            if club_user:
                if obj.club.name.lower() == "bro":
                    try:
                        return GizmoGetUserBalanceService(instance=obj, user_id=club_user.gizmo_id).run()
                    except UserNotFound:
                        return 0
                return GizmoGetUserBalanceService(instance=obj, user_id=club_user.gizmo_id).run()
        return 0

    def get_login(self, obj):
        if self.user:
            club_user = ClubBranchUser.objects.filter(user=self.user, club_branch=obj).first()
            if club_user:
                return club_user.login
        return None

    def get_is_verified(self, obj):
        if self.user:
            club_user = ClubBranchUser.objects.filter(user=self.user, club_branch=obj).first()
            if club_user:
                return bool(club_user.gizmo_id)


class ClubUserSerializer(RequestUserPropertyMixin, serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    def get_user(self, obj):
        if self.user:
            return BaseClubUserSerializer(obj, context=self.context).data


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
    is_booked = serializers.SerializerMethodField()

    class Meta:
        model = ClubComputer
        fields = ('id', 'number', 'is_booked')

    def get_is_booked(self, obj):
        return cache.get(f'BOOKING_STATUS_COMP_{obj.id}') or obj.is_booked


class ClubBranchInfoSerializer(serializers.ModelSerializer):
    hall_name = serializers.CharField(source='name')
    properties = serializers.SerializerMethodField()
    hardware = serializers.SerializerMethodField()
    prices = serializers.SerializerMethodField()
    computers = serializers.SerializerMethodField()

    class Meta:
        model = ClubComputerGroup
        fields = (
            'id',
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
        return ClubComputerSerializer(
            obj.club_branch.computers.filter(group_id=obj.id),
            many=True
        ).data


class ClubComputerListSerializer(serializers.ModelSerializer):
    hall_name = serializers.CharField(source='group.name')
    hall_id = serializers.CharField(source='group.id')

    class Meta:
        model = ClubComputer
        fields = (
            'id',
            'number',
            'is_booked',
            'hall_name',
            'hall_id',
        )


class ClubBranchDetailSerializer(ClubUserSerializer):
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
            'user',
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


class ClubBranchSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source='name')
    club_name = serializers.CharField(source='club.name')

    class Meta:
        model = ClubBranch
        fields = (
            'id',
            'club_name',
            'branch_name'
        )


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
        return obj.club_branch.computers.filter(group_id=obj.id, is_active_session=False, is_locked=False).count()


class ClubBranchListSerializer(ClubUserSerializer):
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
            'image',
            'address',
            'is_favorite',
            'user',
            'landing',
        )

    def get_name(self, obj):
        return obj.club.name

    def get_description(self, obj):
        return obj.club.description

    # def get_landing(self, obj):
    #     halls = []
    #     for group in obj.computer_groups.all():
    #         halls.append(ClubComputerGroupLanding(obj, context={"group_name": group.name}).data)
    #     return halls


class ClubTimePacketListSerializer(serializers.ModelSerializer):
    is_available = serializers.SerializerMethodField()

    class Meta:
        model = ClubTimePacket
        fields = (
            'id',
            'name',
            'price',
            'is_available',
        )

    def get_is_available(self, obj):
        if not obj.available_time_start:
            return True
        return obj.available_time_start <= timezone.now().astimezone().time() <= obj.available_time_end
