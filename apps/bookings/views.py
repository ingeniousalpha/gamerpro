from rest_framework.generics import CreateAPIView, ListAPIView

from apps.bookings.models import Booking
from apps.bookings.serializers import (
    CreateBookingByBalanceSerializer,
    CreateBookingByPaymentSerializer,
    CreateBookingByCardPaymentSerializer,
    BookingListSerializer
)
from apps.common.mixins import PublicJSONRendererMixin, JSONRendererMixin


class CreateBookingByBalanceView(PublicJSONRendererMixin, CreateAPIView):
    queryset = Booking.objects.all()
    serializer_class = CreateBookingByBalanceSerializer


class CreateBookingByPaymentView(PublicJSONRendererMixin, CreateAPIView):
    queryset = Booking.objects.all()
    serializer_class = CreateBookingByPaymentSerializer


class CreateBookingByCardPaymentView(PublicJSONRendererMixin, CreateAPIView):
    queryset = Booking.objects.all()
    serializer_class = CreateBookingByCardPaymentSerializer


class BookingHistoryView(JSONRendererMixin, ListAPIView):
    serializer_class = BookingListSerializer

    def get_queryset(self):
        return Booking.objects.filter(club_user__user=self.request.user).order_by('-created_at')
d