from django.db.models import Sum, Count
from django.shortcuts import render
from rest_framework.generics import ListAPIView
from django.conf import settings
from django.utils import timezone

from apps.common.mixins import PublicJSONRendererMixin
from .models import Document
from .serializers import DocumentListSerializer
from ..bookings.models import Booking


class DocumentListView(PublicJSONRendererMixin, ListAPIView):
    queryset = Document.objects.all()
    serializer_class = DocumentListSerializer
    pagination_class = None


def dashboard_view(request):
    queryset = Booking.objects.filter(is_cancelled=False, payment__isnull=False)
    bookings_count_total = queryset.count()
    today_bookings = queryset.filter(created_at__date=timezone.now().date())
    bookings_count_today = today_bookings.count()
    today_amount = today_bookings.aggregate(Sum('amount'))['amount__sum'] if today_bookings.count() > 0 else 0
    commission_amount = 0
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
