from rest_framework.generics import CreateAPIView, ListAPIView, GenericAPIView, RetrieveAPIView
from rest_framework.response import Response

from apps.bookings.exceptions import BookingNotFound
from apps.bookings.models import Booking
from apps.bookings.serializers import (
    CreateBookingByBalanceSerializer,
    CreateBookingByPaymentSerializer,
    CreateBookingByCardPaymentSerializer,
    BookingSerializer
)
from apps.common.mixins import PublicJSONRendererMixin, JSONRendererMixin
from . import BookingStatuses
from .tasks import gizmo_cancel_booking, gizmo_unlock_computers
from constance import config

from ..integrations.gizmo.users_services import GizmoUpdateComputerStateByUserSessionsService
from ..payments.serializers import BookingProlongSerializer


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
        booking.is_cancelled = True
        booking.status = BookingStatuses.CANCELLED
        booking.save(update_fields=['is_cancelled', 'status'])
        if config.INTEGRATIONS_TURNED_ON:
            gizmo_cancel_booking.delay(booking.uuid)
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
        booking.status = BookingStatuses.PLAYING
        booking.save(update_fields=['status'])
        if config.INTEGRATIONS_TURNED_ON:
            gizmo_unlock_computers.delay(booking.uuid)
        return Response({})


class BookingProlongView(JSONRendererMixin, GenericAPIView):
    serializer_class = BookingProlongSerializer
    queryset = Booking.objects.all()

    def get_object(self):
        obj = self.queryset.filter(uuid=self.kwargs.get('booking_uuid')).first()
        if not obj:
            raise BookingNotFound
        return obj

    def post(self, request, booking_uuid):
        booking = self.get_object()
        serializer = self.get_serializer(data={**request.data, 'booking': booking.id})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({})


class BookingHistoryView(JSONRendererMixin, ListAPIView):
    serializer_class = BookingSerializer

    def get_queryset(self):
        return Booking.objects.filter(club_user__user=self.request.user).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        if queryset.first().is_active:
            GizmoUpdateComputerStateByUserSessionsService(instance=queryset.first().club_branch).run()
            queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class BookingDetailView(JSONRendererMixin, RetrieveAPIView):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer

    def get_object(self):
        obj = self.queryset.filter(uuid=self.kwargs.get('booking_uuid')).first()
        if not obj:
            raise BookingNotFound
        return obj
