from django.shortcuts import render
from rest_framework.generics import ListAPIView, RetrieveAPIView

from apps.clubs.models import Club, ClubBranch
from apps.clubs.serializers import ClubListSerializer, ClubBranchListSerializer, ClubBranchDetailSerializer
from apps.common.mixins import PublicJSONRendererMixin


class ClublistView(PublicJSONRendererMixin, ListAPIView):
    queryset = Club.objects.all()
    serializer_class = ClubListSerializer


class ClubBranchlistView(PublicJSONRendererMixin, ListAPIView):
    queryset = ClubBranch.objects.all()
    serializer_class = ClubBranchListSerializer


class ClubBranchDetailView(PublicJSONRendererMixin, RetrieveAPIView):
    queryset = ClubBranch.objects.all()
    serializer_class = ClubBranchDetailSerializer
