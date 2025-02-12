from django.core.cache import cache
from django.utils import timezone
from django.utils.functional import cached_property
from rest_framework import serializers

from apps.common.serializers import RequestUserPropertyMixin
from . import SoftwareTypes
from .models import (
    Club, ClubBranch, ClubComputer, ClubBranchPrice, ClubBranchProperty, ClubBranchHardware,
    ClubComputerGroup, ClubBranchUser, ClubTimePacket, ClubUserCashback, ClubComputerLayoutGroup
)
from .services import get_cashback
from ..users.services import get_senet_user_balance


class ShortClubUserSerializer(serializers.ModelSerializer):
    account_id = serializers.IntegerField(source='id')

    class Meta:
        model = ClubBranchUser
        fields = ('account_id', 'login')


class BaseClubUserSerializer(RequestUserPropertyMixin, serializers.Serializer):
    login = serializers.SerializerMethodField()
    balance = serializers.SerializerMethodField()
    account_balance = serializers.SerializerMethodField()
    is_verified = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'login',
            'balance',
            'account_balance',
            'is_verified',
        )

    def get_balance(self, obj):
        if self.user:
            return get_cashback(user=self.user, club=obj.club)
        return 0

    def get_account_balance(self, obj):
        if self.user:
            if obj.club.software_type == SoftwareTypes.SENET:
                club_branch_user = ClubBranchUser.objects.filter(user=self.user, club_branch=obj).first()
                return get_senet_user_balance(club_branch_user)
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
                return club_user.is_verified


class ClubUserSerializer(RequestUserPropertyMixin, serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    def get_user(self, obj):
        if obj.club.software_type == SoftwareTypes.SENET:
            club_branch = obj.main_club_branch or obj
        else:
            club_branch = obj
        if self.user and ClubBranchUser.objects.filter(user=self.user, club_branch=club_branch).exists():
            return BaseClubUserSerializer(club_branch, context=self.context).data


class ClubListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Club
        fields = (
            'name',
            'description',
        )


class ClubListV2Serializer(serializers.ModelSerializer):
    # The decision to combine "Club" and "ClubBranch" fields belongs to the project manager a.k.a. Zhalgas

    logo = serializers.SerializerMethodField()
    is_favorite = serializers.SerializerMethodField()
    is_chain = serializers.BooleanField()
    address = serializers.SerializerMethodField()
    free_computer_count = serializers.SerializerMethodField()
    total_computer_count = serializers.SerializerMethodField()

    class Meta:
        model = Club
        fields = (
            'id',
            'name',
            'description',
            'logo',
            'software_type',
            'is_favorite',
            'is_chain',
            'address',
            'free_computer_count',
            'total_computer_count',
        )

    def get_logo(self, obj):
        return self.context.get('request').build_absolute_uri(obj.logo.url) if obj.logo else None

    def get_is_favorite(self, obj):
        # For some unknown reason "favorite clubs" was implemented on frontend side
        return False

    def get_address(self, obj):
        if not obj.is_chain:
            branch = obj.branches.filter(is_active=True, is_turned_on=True).first()
            if branch:
                return branch.address
        return None

    def get_free_computer_count(self, obj):
        if not obj.is_chain:
            branch = obj.branches.filter(is_active=True, is_turned_on=True).first()
            if branch:
                return (
                    branch.computers
                    .filter(is_active_session=False, is_locked=False, is_broken=False, is_deleted=False)
                    .count()
                )
        return None

    def get_total_computer_count(self, obj):
        if not obj.is_chain:
            branch = obj.branches.filter(is_active=True, is_turned_on=True).first()
            if branch:
                return branch.computers.filter(is_deleted=False).count()
        return None


class ClubBranchListV2Serializer(ClubUserSerializer):
    is_favorite = serializers.SerializerMethodField()
    free_computer_count = serializers.SerializerMethodField()
    total_computer_count = serializers.SerializerMethodField()

    class Meta:
        model = ClubBranch
        fields = (
            'id',
            'user',
            'is_favorite',
            'address',
            'free_computer_count',
            'total_computer_count',
        )

    def get_is_favorite(self, obj):
        # For some unknown reason "favorite club branches" was implemented on frontend side
        return False

    def get_free_computer_count(self, obj):
        return obj.computers.filter(is_active_session=False, is_locked=False, is_broken=False, is_deleted=False).count()

    def get_total_computer_count(self, obj):
        return obj.computers.filter(is_deleted=False).count()


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
            obj.club_branch.computers.filter(group_id=obj.id, is_deleted=False),
            many=True
        ).data


class ClubBranchLayoutInfoSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    hall_name = serializers.CharField(source='name')
    properties = serializers.SerializerMethodField()
    hardware = serializers.SerializerMethodField()
    prices = serializers.SerializerMethodField()
    computers = serializers.SerializerMethodField()

    class Meta:
        model = ClubComputerLayoutGroup
        fields = (
            'id',
            'hall_name',
            'prices',
            'properties',
            'hardware',
            'computers'
        )

    def get_prices(self, obj):
        return []

    def get_properties(self, obj):
        return []

    def get_hardware(self, obj):
        return []

    def get_id(self, obj):
        computer = obj.computers.filter(is_deleted=False).first()
        if computer.group: return computer.group.id

    def get_computers(self, obj):
        return ClubComputerSerializer(
            obj.computers.filter(is_deleted=False),
            many=True
        ).data


class ClubComputerListSerializer(serializers.ModelSerializer):
    hall_name = serializers.SerializerMethodField()
    hall_id = serializers.SerializerMethodField()
    is_booked = serializers.SerializerMethodField()

    class Meta:
        model = ClubComputer
        fields = (
            'id',
            'number',
            'is_booked',
            'hall_name',
            'hall_id',
        )

    def get_is_booked(self, obj):
        return cache.get(f'BOOKING_STATUS_COMP_{obj.id}') or obj.is_booked

    def get_hall_id(self, obj):
        if obj.group:
            return str(obj.group.id)

    def get_hall_name(self, obj):
        if obj.group:
            return obj.group.name
        return ""


class ClubBranchDetailSerializer(ClubUserSerializer):
    name = serializers.SerializerMethodField()
    is_favorite = serializers.BooleanField(default=False)
    halls_info = serializers.SerializerMethodField()
    computers = serializers.SerializerMethodField()

    class Meta:
        model = ClubBranch
        fields = (
            'id',
            'name',
            'is_ready',
            'address',
            'is_favorite',
            'user',
            'halls_info',
            'computers',
            'seating_plan'
        )

    def get_name(self, obj):
        return obj.club.name

    def get_computers(self, obj):
        return ClubComputerListSerializer(
            obj.computers.filter(is_deleted=False, group__isnull=False), many=True,
        ).data

    def get_halls_info(self, obj):
        if obj.layout_groups.filter(
            computers__isnull=False,
            computers__is_deleted=False,
            is_available=True
        ).distinct().exists():
            return ClubBranchLayoutInfoSerializer(
                obj.layout_groups.filter(
                    computers__isnull=False,
                    computers__is_deleted=False,
                    is_available=True
                ).distinct(), many=True
            ).data
        return ClubBranchInfoSerializer(
            obj.computer_groups.filter(is_deleted=False), many=True
        ).data

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
        return obj.club_branch.computers.filter(group_id=obj.id, is_deleted=False).count()

    def get_computers_free(self, obj):
        return obj.club_branch.computers.filter(
            group_id=obj.id,
            is_deleted=False,
            is_active_session=False,
            is_locked=False
        ).count()


class ClubComputerLayoutGroupLanding(serializers.ModelSerializer):
    hall_name = serializers.CharField(source='name')
    computers_total = serializers.SerializerMethodField()
    computers_free = serializers.SerializerMethodField()

    class Meta:
        model = ClubComputerLayoutGroup
        fields = (
            'hall_name',
            'computers_total',
            'computers_free',
        )

    def get_computers_total(self, obj):
        return obj.computers.filter(is_deleted=False).count()

    def get_computers_free(self, obj):
        return obj.computers.filter(
            is_deleted=False,
            is_active_session=False,
            is_locked=False
        ).count()


class ClubBranchListSerializer(ClubUserSerializer):
    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    is_favorite = serializers.BooleanField(default=False)
    landing = serializers.SerializerMethodField()

    class Meta:
        model = ClubBranch
        fields = (
            'id',
            'name',
            'description',
            'trader_name',
            'image',
            'address',
            'is_favorite',
            'is_ready',
            'user',
            'extra_data',
            'landing',
            'seating_plan'
        )

    def get_name(self, obj):
        return obj.__str__()

    def get_description(self, obj):
        return obj.club.description

    def get_landing(self, obj):
        if obj.layout_groups.filter(
            computers__isnull=False,
            computers__is_deleted=False,
            is_available=True
        ).distinct().exists():
            return ClubComputerLayoutGroupLanding(
                obj.layout_groups.filter(
                    computers__isnull=False,
                    computers__is_deleted=False,
                    is_available=True
                ).distinct(), many=True
            ).data
        return ClubComputerGroupLanding(
            obj.computer_groups.filter(is_deleted=False), many=True
        ).data


class ClubTimePacketListSerializer(serializers.ModelSerializer):
    price = serializers.SerializerMethodField()
    is_available = serializers.SerializerMethodField()

    class Meta:
        model = ClubTimePacket
        fields = (
            'id',
            'name',
            'description',
            'price',
            'is_available',
        )

    def get_price(self, obj):
        return obj.actual_price

    def get_is_available(self, obj):
        if not obj.available_time_start:
            return True
        return obj.available_time_start <= timezone.now().astimezone().time() <= obj.available_time_end


class ClubUserCashbackSerializer(serializers.ModelSerializer):
    total_amount = serializers.IntegerField(default=0, source="cashback_amount")

    class Meta:
        model = ClubUserCashback
        fields = (
            'total_amount',
        )

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        print("representation: ", representation)
        if representation is None:
            return {
                'total_amount': 0
            }
        return representation



class SeatingPlanSerializer(serializers.ModelSerializer):
    halls = serializers.JSONField()

    class Meta:
        model = ClubBranch
        fields = ["halls"]

    def to_representation(self, instance):
        return {"halls": instance.seating_plan or []}

    def to_internal_value(self, data):
        if "halls" not in data:
            raise serializers.ValidationError({"halls": "Это поле обязательно."})
        return {"seating_plan": data["halls"]}
