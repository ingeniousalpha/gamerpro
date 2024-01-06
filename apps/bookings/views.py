from rest_framework.generics import CreateAPIView, ListAPIView, GenericAPIView, RetrieveAPIView
from rest_framework.response import Response

from apps.bookings.exceptions import BookingNotFound, BookingStatusIsNotAppropriate, UserNeedToVerifyIIN
from apps.bookings.models import Booking
from apps.bookings.serializers import (
    CreateBookingByBalanceSerializer,
    CreateBookingByPaymentSerializer,
    CreateBookingByCardPaymentSerializer,
    BookingSerializer,
    CreateBookingByTimePacketPaymentSerializer,
    CreateBookingByTimePacketCardPaymentSerializer
)
from apps.common.mixins import PublicJSONRendererMixin, JSONRendererMixin
from . import BookingStatuses
from .tasks import gizmo_cancel_booking, gizmo_unlock_computers, gizmo_unlock_computers_and_start_user_session, \
    send_push_about_booking_status
from constance import config

from ..integrations.gizmo.users_services import GizmoUpdateComputerStateByUserSessionsService, \
    GizmoEndUserSessionService
from ..payments import PaymentStatuses
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


class CreateBookingByTimePacketPaymentView(JSONRendererMixin, CreateAPIView):
    queryset = Booking.objects.all()
    serializer_class = CreateBookingByTimePacketPaymentSerializer


class CreateBookingByTimePacketCardPaymentView(JSONRendererMixin, CreateAPIView):
    queryset = Booking.objects.all()
    serializer_class = CreateBookingByTimePacketCardPaymentSerializer


class BookingMixin:
    def get_object(self):
        obj = self.queryset.filter(uuid=self.kwargs.get('booking_uuid')).first()
        if not obj:
            raise BookingNotFound
        return obj


class CancelBookingView(JSONRendererMixin, BookingMixin, GenericAPIView):
    queryset = Booking.objects.all()

    def post(self, request, booking_uuid):
        booking = self.get_object()
        booking.is_cancelled = True
        booking.status = BookingStatuses.CANCELLED
        booking.save(update_fields=['is_cancelled', 'status'])
        if config.INTEGRATIONS_TURNED_ON:
            gizmo_cancel_booking.delay(booking.uuid)
        send_push_about_booking_status.delay(booking.uuid, BookingStatuses.CANCELLED)
        return Response({})


class UnlockBookedComputersView(JSONRendererMixin, BookingMixin, GenericAPIView):
    queryset = Booking.objects.all()

    def options(self, request, *args, **kwargs):
        return Response({})

    def post(self, request, booking_uuid):
        if not config.INTEGRATIONS_TURNED_ON:
            return Response({})

        booking = self.get_object()
        if booking.club_branch.club.name.lower() == "bro" and not booking.club_user.is_verified:
            raise UserNeedToVerifyIIN

        if not booking.use_balance and not booking.payments.filter(status=PaymentStatuses.PAYMENT_APPROVED).exists():
            return Response({})

        elif booking.status == BookingStatuses.CANCELLED:
            return Response({})

        elif booking.status == BookingStatuses.ACCEPTED:
            booking.status = BookingStatuses.PLAYING
            booking.is_starting_session = True
            booking.save(update_fields=['status', 'is_starting_session'])
            gizmo_unlock_computers_and_start_user_session(booking.uuid)
            send_push_about_booking_status.delay(booking.uuid, BookingStatuses.PLAYING)

        elif booking.status == BookingStatuses.SESSION_STARTED:
            gizmo_unlock_computers.delay(booking.uuid)

        return Response({})


class BookingProlongView(JSONRendererMixin, BookingMixin, GenericAPIView):
    serializer_class = BookingProlongSerializer
    queryset = Booking.objects.all()

    def post(self, request, booking_uuid):
        booking = self.get_object()
        serializer = self.get_serializer(data={**request.data, 'booking': booking.id})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({})


class ComputerSessionFinishView(JSONRendererMixin, BookingMixin, GenericAPIView):
    queryset = Booking.objects.all()

    def post(self, request, booking_uuid):
        booking = self.get_object()
        if booking.status not in [BookingStatuses.SESSION_STARTED, BookingStatuses.PLAYING]:
            raise BookingStatusIsNotAppropriate

        booking.status = BookingStatuses.COMPLETED
        booking.save(update_fields=['status'])
        if config.INTEGRATIONS_TURNED_ON:
            GizmoEndUserSessionService(
                instance=booking.club_branch,
                user_id=booking.club_user.gizmo_id
            ).run()
            if booking.status == BookingStatuses.SESSION_STARTED:
                gizmo_unlock_computers.delay(booking.uuid)
        return Response({})


class BookingHistoryView(JSONRendererMixin, ListAPIView):
    serializer_class = BookingSerializer

    def get_queryset(self):
        return Booking.objects.filter(club_user__user=self.request.user).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        if not queryset.exists():
            return Response([])

        if queryset.first().status == BookingStatuses.PLAYING and not queryset.first().is_starting_session:
            GizmoUpdateComputerStateByUserSessionsService(instance=queryset.first().club_branch).run()
            queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class BookingDetailView(JSONRendererMixin, BookingMixin, RetrieveAPIView):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
