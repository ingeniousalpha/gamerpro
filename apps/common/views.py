from django.shortcuts import render
from rest_framework.generics import ListAPIView

from apps.common.mixins import PublicJSONRendererMixin
from .models import Document
from .serializers import DocumentListSerializer


class DocumentListView(PublicJSONRendererMixin, ListAPIView):
    queryset = Document.objects.all()
    serializer_class = DocumentListSerializer
    pagination_class = None
