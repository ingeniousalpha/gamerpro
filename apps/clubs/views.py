from django.shortcuts import render
from rest_framework.generics import ListAPIView, RetrieveAPIView

from apps.clubs.models import Club, ClubBranch
from apps.clubs.serializers import ClubListSerializer, ClubBranchListSerializer, ClubBranchDetailSerializer
from apps.clubs.tasks import _sync_gizmo_computers_state_of_club_branch
from apps.common.mixins import PublicJSONRendererMixin
from apps.pipeline.gizmo.computers_services import GizmoGetComputersService


class ClublistView(PublicJSONRendererMixin, ListAPIView):
    queryset = Club.objects.all()
    serializer_class = ClubListSerializer


class ClubBranchlistView(PublicJSONRendererMixin, ListAPIView):
    queryset = ClubBranch.objects.all()
    serializer_class = ClubBranchListSerializer


class ClubBranchDetailView(PublicJSONRendererMixin, RetrieveAPIView):
    queryset = ClubBranch.objects.all()
    serializer_class = ClubBranchDetailSerializer

    def retrieve(self, request, *args, **kwargs):
        _sync_gizmo_computers_state_of_club_branch(self.get_object())
        return super().retrieve(request, *args, **kwargs)
