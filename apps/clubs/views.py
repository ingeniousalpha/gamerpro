from django.db.models import Q, F
from django.utils import timezone
from rest_framework.generics import ListAPIView, RetrieveAPIView

from apps.clubs.models import Club, ClubBranch, ClubTimePacket, ClubUserCashback
from apps.clubs.serializers import (
    ClubListSerializer, ClubBranchListSerializer, ClubBranchDetailSerializer, ClubTimePacketListSerializer,
    ClubUserCashbackSerializer
)
from apps.clubs.tasks import _sync_club_branch_computers
from apps.common.mixins import PublicJSONRendererMixin, JSONRendererMixin
from apps.common.pagination import ClubsPagination


class ClublistView(PublicJSONRendererMixin, ListAPIView):
    queryset = Club.objects.all()
    serializer_class = ClubListSerializer


class ClubBranchlistView(PublicJSONRendererMixin, ListAPIView):
    pagination_class = ClubsPagination
    queryset = (ClubBranch.objects.filter(is_active=True, is_turned_on=True)
                .filter(club__is_bro_chain=False)
                .order_by('-priority'))
    serializer_class = ClubBranchListSerializer

    def get_queryset(self):
        if self.request.GET.get('city'):
            return self.queryset.filter(Q(city=self.request.GET.get('city')) & Q(city__is_active=True))
        return self.queryset


class BROClubBranchlistView(PublicJSONRendererMixin, ListAPIView):
    pagination_class = ClubsPagination
    queryset = (ClubBranch.objects.filter(is_active=True, is_turned_on=True)
                .filter(club__is_bro_chain=True)
                .order_by('-priority'))
    serializer_class = ClubBranchListSerializer

    def get_queryset(self):
        if self.request.GET.get('city'):
            return self.queryset.filter(Q(city=self.request.GET.get('city')) & Q(city__is_active=True))
        return self.queryset


class ClubBranchDetailView(PublicJSONRendererMixin, RetrieveAPIView):
    queryset = ClubBranch.objects.all()
    serializer_class = ClubBranchDetailSerializer

    def retrieve(self, request, *args, **kwargs):
        _sync_club_branch_computers(self.get_object())
        return super().retrieve(request, *args, **kwargs)


class ClubBranchTimePacketListView(JSONRendererMixin, ListAPIView):
    queryset = ClubTimePacket.objects.all()
    serializer_class = ClubTimePacketListSerializer
    pagination_class = None

    def get_queryset(self):
        today = timezone.now().astimezone().weekday() + 1
        res_queryset = super().get_queryset().filter(
            club_computer_group_id=self.kwargs.get('hall_id'),
            is_active=True, available_days__number=today,
        ).filter(
            (Q(available_time_start__lte=timezone.now().astimezone().time()) & Q(
                available_time_end__gte=timezone.now().astimezone().time())) |
            (Q(available_time_start__gte=F('available_time_end')) & (
                    Q(available_time_end__gte=timezone.now().astimezone().time()) | Q(
                available_time_start__lte=timezone.now().astimezone().time()))
             )
        ).order_by('priority')

        if today == 2:
            extra_queryset = super().get_queryset().filter(
                club_computer_group_id=self.kwargs.get('hall_id'),
                is_active=True, available_days__number=7,
            ).filter(Q(available_time_start__gte=F('available_time_end')) &
                     Q(available_time_end__gt=timezone.now().time()))
            minus_queryset = super().get_queryset().filter(
                club_computer_group_id=self.kwargs.get('hall_id'),
                is_active=True, available_days__number=today,
            ).filter(Q(available_time_start__gte=F('available_time_end')) &
                     Q(available_time_start__gt=timezone.now().time()))
            res_queryset = (res_queryset | extra_queryset).distinct()
            if minus_queryset:
                res_queryset = res_queryset.exclude(pk__in=minus_queryset.values('pk'))
            return res_queryset

        return res_queryset


class ClubUserCashbackView(JSONRendererMixin, RetrieveAPIView):
    queryset = ClubUserCashback.objects.all()
    serializer_class = ClubUserCashbackSerializer

    def get_object(self):
        obj = super().get_queryset().filter(
            club_id=self.kwargs.get('pk'),
            user=self.request.user
        ).first()
        if not obj:
            obj = ClubUserCashback.objects.create(
                club_id=self.kwargs.get('pk'),
                user=self.request.user,
            )
        return obj
