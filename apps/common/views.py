from django.db.models import Sum, Count
from django.shortcuts import render
from rest_framework.generics import ListAPIView, GenericAPIView
from django.conf import settings
from django.utils import timezone

from apps.common.mixins import PublicJSONRendererMixin
from rest_framework.response import Response
from .models import Document, AppVersion, City
from .serializers import DocumentListSerializer, CitiesListSerializer
from ..bookings.models import Booking
from ..clubs.models import ClubBranch


class DocumentListView(PublicJSONRendererMixin, ListAPIView):
    queryset = Document.objects.all()
    serializer_class = DocumentListSerializer
    pagination_class = None


class DocumentPrivacyPolicyView(PublicJSONRendererMixin, GenericAPIView):
    def get(self, request):
        trader_name = None
        if request.GET.get('club_branch'):
            club_branch_id = int(request.GET.get('club_branch'))
            club_branch = ClubBranch.objects.filter(id=club_branch_id).first()
            if club_branch:
                trader_name = club_branch.trader_name
        return render(request, "privacy_policy.html", {
            "trader_name": trader_name
        })


class DocumentPublicOfferView(PublicJSONRendererMixin, GenericAPIView):
    def get(self, request):
        trader_name = None
        if request.GET.get('club_branch'):
            club_branch_id = int(request.GET.get('club_branch'))
            club_branch = ClubBranch.objects.filter(id=club_branch_id).first()
            if club_branch:
                trader_name = club_branch.trader_name
        return render(request, "public_offer.html", {
            "trader_name": trader_name
        })


class DocumentPaymentPolicyView(PublicJSONRendererMixin, GenericAPIView):
    def get(self, request):
        trader_name = None
        if request.GET.get('club_branch'):
            club_branch_id = int(request.GET.get('club_branch'))
            club_branch = ClubBranch.objects.filter(id=club_branch_id).first()
            if club_branch:
                trader_name = club_branch.trader_name
        return render(request, "payment_policy.html", {
            "trader_name": trader_name
        })


class CitiesListView(PublicJSONRendererMixin, ListAPIView):
    queryset = City.objects.filter(is_active=True)
    serializer_class = CitiesListSerializer
    pagination_class = None


class BroAppVersionsView(PublicJSONRendererMixin, GenericAPIView):
    def get(self, request):
        app_versions = AppVersion.objects.filter(app="BRO")
        return Response({
            "IOS": app_versions.filter(platform="IOS").last().number,
            "ANDROID": app_versions.filter(platform="ANDROID").last().number,
        })


class LobbyAppVersionsView(PublicJSONRendererMixin, GenericAPIView):
    def get(self, request):
        app_versions = AppVersion.objects.filter(app="Lobby")
        return Response({
            "IOS": app_versions.filter(platform="IOS").last().number,
            "ANDROID": app_versions.filter(platform="ANDROID").last().number,
        })


def dashboard_view(request):
    queryset = Booking.objects.all()
    bookings_count_total = queryset.count()
    today_bookings = queryset.filter(created_at__date=timezone.now().date())
    bookings_count_today = today_bookings.count()
    today_amount = today_bookings.aggregate(Sum('amount'))['amount__sum'] if today_bookings.count() > 0 else 0
    commission_amount = today_bookings.aggregate(Sum('commission_amount'))['commission_amount__sum'] if today_bookings.count() > 0 else 0
    dates = queryset.filter(
        created_at__date__gte=timezone.now() - timezone.timedelta(days=10)
    ).values('created_at__date').annotate(bookings_count=Count('id')).order_by('created_at__date')
    print(dates)
    dates_list = []
    bookings_count_list = []
    for item in dates:
        dates_list.append(item['created_at__date'].strftime("%d.%m"))
        bookings_count_list.append(item['bookings_count'])

    print(dates_list)
    print(bookings_count_list)
    return render(request, "dashboard.html", {
        "bookings_count_total": bookings_count_total,
        "bookings_count_today": bookings_count_today,
        "today_amount": today_amount,
        "commission_amount": commission_amount,
        "dates_list": dates_list,
        "bookings_count_list": bookings_count_list,
    })


def stats_view(request):
    return render(request, "stats.html")
