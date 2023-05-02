from django.shortcuts import render
from rest_framework.generics import ListAPIView, RetrieveAPIView

from apps.clubs.models import Club, ClubBranch
from apps.clubs.serializers import ClubListSerializer, ClubBranchListSerializer, ClubBranchDetailSerializer
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
        GizmoGetComputersService(instance=self.get_object()).run()
        return super().retrieve(request, *args, **kwargs)
