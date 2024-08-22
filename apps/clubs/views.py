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
        current_time = timezone.now().astimezone().time()
        current_day = timezone.now().weekday() + 1  # Monday=0, Sunday=6

        return super().get_queryset().filter(
            club_computer_group_id=self.kwargs.get('hall_id'),
            is_active=True,
            available_days__number=current_day,
        ).filter(
            # Case 1: Time packet starts and ends on the same day
            Q(available_time_start__lte=current_time, available_time_end__gte=current_time) |

            # Case 2: Time packet starts before midnight and ends after midnight (spanning two days)
            Q(available_time_start__gte=F('available_time_end')) & (
                    Q(available_time_end__gte=current_time) | Q(available_time_start__lte=current_time)
            )
        ).exclude(
            # Exclude time packets ending on the previous day
            Q(available_time_end__lte=current_time) & Q(available_time_start__gte=F('available_time_end'))
        ).order_by('priority')


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
