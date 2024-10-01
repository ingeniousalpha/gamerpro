from datetime import datetime

from django.db.models import Sum, Count, Q, F, Func
from django.shortcuts import render
from django.utils import timezone
from rest_framework.generics import ListAPIView, GenericAPIView
from rest_framework.response import Response

from apps.common.mixins import PublicJSONRendererMixin
from .models import Document, AppVersion, City
from .serializers import DocumentListSerializer, CitiesListSerializer
from ..bookings.models import Booking, BookingStatuses
from ..clubs.models import ClubBranch
from ..payments.models import Payment, PaymentStatuses
from ..users.models import User

MONTHS_NAMES = {
    "1": "Январь",
    "2": "Февраль",
    "3": "Март",
    "4": "Апрель",
    "5": "Май",
    "6": "Июнь",
    "7": "Июль",
    "8": "Август",
    "9": "Сентябрь",
    "10": "Октябрь",
    "11": "Ноябрь",
    "12": "Декабрь"
}


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


class MonthYear(Func):
    function = 'CONCAT'
    template = "%(function)s(EXTRACT(YEAR FROM %(expressions)s), '.', EXTRACT(MONTH FROM %(expressions)s))"


def get_month_str(month_dot_year):
    year, month = month_dot_year.split('.')
    return f"{MONTHS_NAMES.get(month)} {year}"


def dashboard_view(request):
    period = request.GET.get('period')  # today/last_week/last_month/last_year
    group_by_field = 'created_at__date'
    if period == 'today':
        filter_period = timezone.now().date()
    elif period == 'last_week':
        filter_period = timezone.now() - timezone.timedelta(days=7)
    elif period == 'last_year':
        group_by_field = 'month_year'
        filter_period = timezone.now() - timezone.timedelta(days=365)
    else:
        period = 'last_month'
        filter_period = timezone.now() - timezone.timedelta(days=30)

    bookings_total = Booking.objects.filter(created_at__gte=filter_period)
    users_total = User.objects.filter(created_at__gte=filter_period)
    users_count_total = users_total.count()
    successful_bookings = bookings_total.filter(
        Q(payments__status=PaymentStatuses.PAYMENT_APPROVED) | Q(use_cashback=True)
    ).filter(created_at__gte=filter_period)
    cancelled_bookings = successful_bookings.filter(is_cancelled=True)
    bookings_total_count = bookings_total.count()
    bookings_successful_count = successful_bookings.count()
    bookings_cancelled_count = cancelled_bookings.count()
    bookings_successful_revenue_amount = successful_bookings.exclude(is_cancelled=True).aggregate(
        Sum('total_amount')
    )['total_amount__sum'] or 0

    if period == 'last_year':
        dates = bookings_total.annotate(month_year=MonthYear('created_at')).values(group_by_field).annotate(
            bookings_count=Count('id')).order_by(group_by_field)
        payments_dates = Payment.objects.filter(
            status=PaymentStatuses.PAYMENT_APPROVED, created_at__gte=filter_period
        ).annotate(month_year=MonthYear('created_at')).values(group_by_field).annotate(
            payments_count=Count('id')).order_by(group_by_field)
        users_dates = users_total.annotate(month_year=MonthYear('created_at')).values(group_by_field).annotate(
            users_count=Count('id')).order_by(group_by_field)
    else:
        dates = bookings_total.values(group_by_field).annotate(bookings_count=Count('id')).order_by(group_by_field)
        payments_dates = Payment.objects.filter(
            status=PaymentStatuses.PAYMENT_APPROVED, created_at__gte=filter_period
        ).values(group_by_field).annotate(payments_count=Count('id')).order_by(group_by_field)
        users_dates = users_total.values(group_by_field).annotate(users_count=Count('id')).order_by(group_by_field)

    bookings_dates_list = []
    bookings_count_list = []
    for item in dates:
        bookings_dates_list.append(get_month_str(item[group_by_field]) if period=="last_year" else item[group_by_field])
        bookings_count_list.append(item['bookings_count'])

    payments_dates_list = []
    payments_count_list = []
    for item in payments_dates:
        payments_dates_list.append(get_month_str(item[group_by_field]) if period=="last_year" else item[group_by_field])
        payments_count_list.append(item['payments_count'])

    users_dates_list = []
    users_count_list = []
    for item in users_dates:
        users_dates_list.append(get_month_str(item[group_by_field]) if period=="last_year" else item[group_by_field])
        users_count_list.append(item['users_count'])

    bookings_summary_table = (Booking.objects
                              .select_related('club_branch')
                              .filter(created_at__gte=filter_period)
                              .values('club_branch__name').annotate(
        amount_of_booking_tries=Count('id'),
        amount_of_successful_bookings=Count('id', filter=(
                Q(payments__status=PaymentStatuses.PAYMENT_APPROVED) | Q(use_cashback=True)
        )),
        amount_of_cancelled_successful_bookings=Count('id', filter=(
                Q(payments__status=PaymentStatuses.PAYMENT_APPROVED) | Q(use_cashback=True))
                & Q(is_cancelled=True)),
        amount_of_successful_revenue=Sum('total_amount', filter=Q(status__in=[
            BookingStatuses.ACCEPTED,
            BookingStatuses.SESSION_STARTED,
            BookingStatuses.PLAYING,
            BookingStatuses.COMPLETED
        ]) & (Q(payments__status=PaymentStatuses.PAYMENT_APPROVED) | Q(use_cashback=True)) & Q(is_cancelled=False)),
        amount_of_successful_bookings_with_cashback=Count('id', filter=Q(status__in=[
            BookingStatuses.ACCEPTED, 
            BookingStatuses.SESSION_STARTED, 
            BookingStatuses.PLAYING, 
            BookingStatuses.COMPLETED
        ]) & Q(use_cashback=True))
    ).order_by('-amount_of_successful_bookings'))

    return render(request, "dashboard.html", {
        "period": period,
        "bookings_total_count": bookings_total_count,
        "bookings_successful_count": bookings_successful_count,
        "bookings_cancelled_count": bookings_cancelled_count,
        "bookings_successful_revenue_amount": bookings_successful_revenue_amount,
        "users_count_total": users_count_total,
        "bookings_dates_list": bookings_dates_list,
        "bookings_count_list": bookings_count_list,
        "payments_dates_list": payments_dates_list,
        "payments_count_list": payments_count_list,
        "users_dates_list": users_dates_list,
        "users_count_list": users_count_list,
        "bookings_summary_table": bookings_summary_table
    })


def reports_view(request):
    club_branch = request.GET.get('club_branch')
    start_datetime = request.GET.get('start_datetime')
    end_datetime = request.GET.get('end_datetime')
    use_cashback = request.GET.get('use_cashback') == 'on'
    conditions = Q()
    if club_branch:
        conditions = conditions & Q(club_branch_name=club_branch)
    if start_datetime:
        conditions = conditions & Q(booking_created_at__gte=start_datetime)
    if end_datetime:
        conditions = conditions & Q(booking_created_at__lte=end_datetime)
    if not use_cashback:
        conditions = conditions & ~Q(booking__use_cashback=True)
    payments = (
        Payment.objects
        .select_related('booking', 'booking__club_branch')
        .annotate(
            club_branch_name=F('booking__club_branch__name'),
            booking_uuid=F('booking__uuid'),
            booking_created_at=F('booking__created_at'),
            booking_total_amount=F('booking__total_amount')
        )
        .filter(conditions)
        .order_by('booking_created_at', 'club_branch_name', 'created_at')
    )
    return render(
        request=request,
        template_name='reports.html',
        context={
            "club_branches": ClubBranch.objects.order_by('name').values_list('name', flat=True),
            "club_branch": club_branch,
            "start_datetime": start_datetime,
            "end_datetime": end_datetime,
            "use_cashback": use_cashback,
            "payments": payments,
            "total_amount": payments.aggregate(total_amount_sum=Sum('booking_total_amount')).get('total_amount_sum'),
        }
    )


def stats_view(request):
    return render(request, "stats.html")
