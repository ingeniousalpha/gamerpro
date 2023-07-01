from rest_framework.generics import CreateAPIView, ListAPIView, GenericAPIView
from rest_framework.response import Response

from apps.bookings.exceptions import BookingNotFound
from apps.bookings.models import Booking
from apps.bookings.serializers import (
    CreateBookingByBalanceSerializer,
    CreateBookingByPaymentSerializer,
    CreateBookingByCardPaymentSerializer,
    BookingListSerializer
)
from apps.common.mixins import PublicJSONRendererMixin, JSONRendererMixin
from .tasks import gizmo_cancel_booking, gizmo_unlock_computers


class CreateBookingByBalanceView(PublicJSONRendererMixin, CreateAPIView):
    queryset = Booking.objects.all()
    serializer_class = CreateBookingByBalanceSerializer


class CreateBookingByPaymentView(PublicJSONRendererMixin, CreateAPIView):
    queryset = Booking.objects.all()
    serializer_class = CreateBookingByPaymentSerializer


class CreateBookingByCardPaymentView(PublicJSONRendererMixin, CreateAPIView):
    queryset = Booking.objects.all()
    serializer_class = CreateBookingByCardPaymentSerializer


class CancelBookingView(JSONRendererMixin, GenericAPIView):
    queryset = Booking.objects.all()

    def get_object(self):
        obj = self.queryset.filter(uuid=self.kwargs.get('booking_uuid')).first()
        if not obj:
            raise BookingNotFound
        return obj

    def post(self, request, booking_uuid):
        booking = self.get_object()
        # gizmo_cancel_booking.delay(booking.uuid)
        return Response({})


class UnlockBookedComputersView(JSONRendererMixin, GenericAPIView):
    queryset = Booking.objects.all()

    def get_object(self):
        obj = self.queryset.filter(uuid=self.kwargs.get('booking_uuid')).first()
        if not obj:
            raise BookingNotFound
        return obj

    def post(self, request, booking_uuid):
        booking = self.get_object()
        # gizmo_unlock_computers.delay(booking.uuid)
        return Response({})


class BookingHistoryView(JSONRendererMixin, ListAPIView):
    serializer_class = BookingListSerializer

    def get_queryset(self):
        return Booking.objects.filter(club_user__user=self.request.user).order_by('-created_at')
