from django.db.models import Sum, Count, Q, F, CharField, Value
from django.db.models.functions import Concat
from django.shortcuts import render
from rest_framework.generics import ListAPIView, GenericAPIView
from django.conf import settings
from django.utils import timezone

from apps.common.mixins import PublicJSONRendererMixin
from rest_framework.response import Response
from .models import Document, AppVersion, City
from .services import str_to_datetime
from .serializers import DocumentListSerializer, CitiesListSerializer
from ..bookings.models import Booking, BookingStatuses
from ..clubs.models import ClubBranch
from ..payments.models import Payment, PaymentStatuses
from ..users.models import User

from urllib.parse import unquote


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
        
    successful_payments = Payment.objects.filter(status=PaymentStatuses.PAYMENT_APPROVED)
    payments_dates = successful_payments.filter(
        created_at__date__gte=timezone.now() - timezone.timedelta(days=10)
    ).values('created_at__date').annotate(payments_count=Count('id')).order_by('created_at__date')

    payments_dates_list = []
    payments_count_list = []
    for item in payments_dates:
        payments_dates_list.append(item['created_at__date'].strftime("%d.%m"))
        payments_count_list.append(item['payments_count'])

    
    all_users = User.objects.all()
    users_count_total = all_users.count()
    users_dates = all_users.filter(
        created_at__date__gte=timezone.now() - timezone.timedelta(days=10)
    ).values('created_at__date').annotate(users_count=Count('id')).order_by('created_at__date')

    users_dates_list = []
    users_count_list = []
    for item in users_dates:
        users_dates_list.append(item['created_at__date'].strftime("%d.%m"))
        users_count_list.append(item['users_count'])

    
    bookings_summary_table = Booking.objects.select_related('club_branch').values('club_branch__name').annotate(
        amount_of_successful_bookings=Count('id', filter=Q(status__in=[
            BookingStatuses.ACCEPTED, 
            BookingStatuses.SESSION_STARTED, 
            BookingStatuses.PLAYING, 
            BookingStatuses.COMPLETED
        ])),
        amount_of_not_cancelled_successful_bookings=Count('id', filter=Q(status__in=[
            BookingStatuses.ACCEPTED, 
            BookingStatuses.SESSION_STARTED, 
            BookingStatuses.PLAYING, 
            BookingStatuses.COMPLETED
        ]) & Q(is_cancelled=False)),
        amount_of_successful_bookings_with_cashback=Count('id', filter=Q(status__in=[
            BookingStatuses.ACCEPTED, 
            BookingStatuses.SESSION_STARTED, 
            BookingStatuses.PLAYING, 
            BookingStatuses.COMPLETED
        ]) & Q(use_cashback=True))
    ).order_by('amount_of_successful_bookings')

    

    print(dates_list)
    print(bookings_count_list)
    return render(request, "dashboard.html", {
        "bookings_count_total": bookings_count_total,
        "bookings_count_today": bookings_count_today,
        "today_amount": today_amount,
        "commission_amount": commission_amount,
        "users_count_total": users_count_total,
        "dates_list": dates_list,
        "bookings_count_list": bookings_count_list,
        "payments_dates_list": payments_dates_list,
        "payments_count_list": payments_count_list,
        "users_dates_list": users_dates_list,
        "users_count_list": users_count_list,
        "bookings_summary_table": bookings_summary_table
    })

def reports_view(request):
    payments_reports_table = Payment.objects.select_related('booking__club_branch').annotate(
        club_branch=F('booking__club_branch__name'),
        payment_uuid=F('uuid'),
        payment_amount=F('amount'),
        payment_status=F('status'),
        payment_created_at=F('created_at')
        ).values(
            'club_branch',
            'payment_uuid',
            'payment_amount',
            'payment_status',
            'payment_created_at'
            )
    
    start_date = request.GET.get('start_date', '')
    start_time = request.GET.get('start_time', '')
    end_date = request.GET.get('end_date', '')
    end_time = request.GET.get('end_time', '')
    club_branch = request.GET.get('club_branch', '')
    
    '''start_date = timezone.datetime.strptime(start_date, '%Y-%m-%d').date()
    end_date = timezone.datetime.strptime(end_date, '%Y-%m-%d').date()

    start_time = start_time + ':00'
    start_time = timezone.datetime.strptime(start_time, '%H:%M:%S').time()

    end_time = end_time + ':00'
    end_time = timezone.datetime.strptime(end_time, '%H:%M:%S').time()'''


    if start_date:
        payments_reports_table = payments_reports_table.filter(payment_created_at__date__gte=start_date)
    if start_time:
        payments_reports_table = payments_reports_table.filter(payment_created_at__time__gte=start_time)
    if end_date:
        payments_reports_table = payments_reports_table.filter(payment_created_at__date__lte=end_date)
    if end_time:
        payments_reports_table = payments_reports_table.filter(payment_created_at__time__lte=end_time)
    if club_branch:
        payments_reports_table = payments_reports_table.filter(club_branch__icontains=club_branch)


    club_branches = ClubBranch.objects.values_list('name', flat=True).distinct()

    return render(request, 'reports.html', {
        'payments_reports_table': payments_reports_table,
        'start_date': start_date,
        'start_time': start_time,
        'end_date': end_date,
        'end_time': end_time,
        'club_branch': club_branch,
        'club_branches': club_branches,

    })



def stats_view(request):
    return render(request, "stats.html")
