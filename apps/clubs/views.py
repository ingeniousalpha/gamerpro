import pytz
from datetime import time
from django.db.models import Q, F
from django.utils import timezone
from rest_framework.generics import ListAPIView, RetrieveAPIView

from apps.clubs.models import Club, ClubBranch, ClubTimePacket, ClubUserCashback
from apps.clubs.serializers import ClubListSerializer, ClubBranchListSerializer, ClubBranchDetailSerializer, \
    ClubTimePacketListSerializer, ClubUserCashbackSerializer
from apps.clubs.tasks import _sync_gizmo_computers_state_of_club_branch
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
        _sync_gizmo_computers_state_of_club_branch(self.get_object())
        return super().retrieve(request, *args, **kwargs)


class ClubBranchTimePacketListView(JSONRendererMixin, ListAPIView):
    queryset = ClubTimePacket.objects.all()
    serializer_class = ClubTimePacketListSerializer
    pagination_class = None

    def get_queryset(self):
        almaty_tz = pytz.timezone('Asia/Almaty')
        current_time = timezone.now().astimezone(almaty_tz).time()
        current_day = timezone.now().astimezone(almaty_tz).weekday() + 1  # Monday=0, Sunday=6
        previous_day = current_day - 1 if current_day > 1 else 7
        next_day = current_day + 1 if current_day < 7 else 1

        queryset = super().get_queryset().filter(
            club_computer_group_id=self.kwargs.get('hall_id'),
            is_active=True,
        ).filter(
            # Packets that are valid on the current day and within the time range
            (Q(available_days__number=current_day) &
             Q(available_time_start__lte=current_time) &
             Q(available_time_end__gte=current_time)) |

            # Packets that started on the previous day and are still active
            (Q(available_days__number=previous_day) &
             Q(available_time_start__gte=time(22, 0)) &
             Q(available_time_end__lte=time(5, 0)) &
             Q(available_time_end__gte=current_time)) |

            # Packets that are valid on the next day after midnight
            (Q(available_days__number=next_day) &
             Q(available_time_start__gte=F('available_time_end')) &
             Q(available_time_end__gte=current_time))
        ).exclude(
            # Exclude packets like Packet88 until their start time
            Q(available_days__number=current_day) &
            Q(available_time_start__gte=time(22, 0)) &
            Q(available_time_end__lte=time(5, 0)) &
            Q(available_time_start__gte=current_time)
        ).order_by('priority').distinct()

        return queryset


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
