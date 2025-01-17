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
    CreateBookingByTimePacketCardPaymentSerializer,
    CreateBookingByCashbackSerializer, CreateBookingByTimePacketKaspiSerializer, CreateBookingForFreeSerializer
)
from apps.common.mixins import PublicJSONRendererMixin, JSONRendererMixin
from . import BookingStatuses
from .tasks import cancel_booking, unlock_computers, gizmo_unlock_computers_and_start_user_session, \
    send_push_about_booking_status
from constance import config

from ..clubs import SoftwareTypes
from ..clubs.exceptions import UnavailableForSenet
from ..clubs.models import DelayedTimeSetting
from ..integrations.gizmo.users_services import GizmoUpdateComputerStateByUserSessionsService, \
    GizmoEndUserSessionService
from ..integrations.onevision.payment_services import OVInitPaymentService
from ..payments import PaymentStatuses
from ..payments.exceptions import OVGetPaymentURLFailed
from ..payments.serializers import BookingProlongSerializer, BookingProlongByTimePacketSerializer


class BookingMixin:
    def get_object(self):
        obj = (
            self.queryset
            .filter(uuid=self.kwargs.get('booking_uuid'))
            .select_related('club_user__user', 'club_branch__club')
            .first()
        )
        if not obj:
            raise BookingNotFound
        return obj


class CreateBookingByBalanceView(PublicJSONRendererMixin, CreateAPIView):
    queryset = Booking.objects.all()
    serializer_class = CreateBookingByBalanceSerializer


class CreateBookingByPaymentView(PublicJSONRendererMixin, CreateAPIView):
    queryset = Booking.objects.all()
    serializer_class = CreateBookingByPaymentSerializer


class CreateBookingByCardPaymentView(PublicJSONRendererMixin, CreateAPIView):
    queryset = Booking.objects.all()
    serializer_class = CreateBookingByCardPaymentSerializer


class CreateBookingByCashbackView(JSONRendererMixin, CreateAPIView):
    queryset = Booking.objects.all()
    serializer_class = CreateBookingByCashbackSerializer

    def get_serializer_context(self):
        return {
            'request': self.request,
            'booking_method': 'by_cashback'
        }


class CreateBookingByTimePacketPaymentView(JSONRendererMixin, CreateAPIView):
    queryset = Booking.objects.all()
    serializer_class = CreateBookingByTimePacketPaymentSerializer


class CreateBookingByTimePacketKaspiView(JSONRendererMixin, CreateAPIView):
    queryset = Booking.objects.all()
    serializer_class = CreateBookingByTimePacketKaspiSerializer


class CreateBookingByTimePacketCardPaymentView(JSONRendererMixin, CreateAPIView):
    queryset = Booking.objects.all()
    serializer_class = CreateBookingByTimePacketCardPaymentSerializer


class RetryPaymentForBookingByTimePacketView(JSONRendererMixin, BookingMixin, GenericAPIView):
    queryset = Booking.objects.all()

    def post(self, request, booking_uuid):
        booking = self.get_object()
        payment_url = OVInitPaymentService(
            instance=booking,
            club_branch=booking.club_branch,
        ).run()
        if payment_url:
            return Response({
                "booking_uuid": str(booking_uuid),
                "payment_url": payment_url
            })
        else:
            raise OVGetPaymentURLFailed


class CancelBookingView(JSONRendererMixin, BookingMixin, GenericAPIView):
    queryset = Booking.objects.all()

    def post(self, request, booking_uuid):
        booking = self.get_object()
        booking.is_cancelled = True
        booking.status = BookingStatuses.CANCELLED
        booking.save(update_fields=['is_cancelled', 'status'])
        if booking.club_branch.club.software_type == SoftwareTypes.GIZMO and not booking.club_user.is_verified:
            DelayedTimeSetting.objects.create(
                booking=booking,
                user=booking.club_user.user,
                club=booking.club_branch.club,
                time_packet=booking.time_packet,
            )
        if config.INTEGRATIONS_TURNED_ON:
            cancel_booking.delay(booking.uuid)
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

        if not booking.use_cashback and not booking.payments.filter(status=PaymentStatuses.PAYMENT_APPROVED).exists():
            return Response({})

        elif booking.status == BookingStatuses.CANCELLED:
            return Response({})

        elif booking.status == BookingStatuses.ACCEPTED:
            if booking.club_branch.club.software_type == SoftwareTypes.GIZMO:
                gizmo_unlock_computers_and_start_user_session(booking.uuid)
                booking.status = BookingStatuses.PLAYING
                booking.is_starting_session = True
                booking.save(update_fields=['status', 'is_starting_session'])
            elif booking.club_branch.club.software_type == SoftwareTypes.SENET:
                unlock_computers.delay(booking.uuid)
                booking.status = BookingStatuses.COMPLETED
                booking.save(update_fields=['status'])
            send_push_about_booking_status.delay(booking.uuid, BookingStatuses.PLAYING)

        elif (
            booking.status == BookingStatuses.SESSION_STARTED
            and booking.club_branch.club.software_type == SoftwareTypes.GIZMO
        ):
            booking.status = BookingStatuses.PLAYING
            booking.save(update_fields=['status'])
            unlock_computers.delay(booking.uuid)

        return Response({})


class BookingProlongView(JSONRendererMixin, BookingMixin, GenericAPIView):
    serializer_class = BookingProlongSerializer
    queryset = Booking.objects.all()

    def post(self, request, booking_uuid):
        booking = self.get_object()
        if booking.club_branch.club.software_type == SoftwareTypes.SENET:
            raise UnavailableForSenet
        serializer = self.get_serializer(data={**request.data, 'booking': booking.id})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({})


class BookingProlongByTimePacketView(JSONRendererMixin, BookingMixin, GenericAPIView):
    serializer_class = BookingProlongByTimePacketSerializer
    queryset = Booking.objects.all()

    def post(self, request, booking_uuid):
        booking = self.get_object()
        if booking.club_branch.club.software_type == SoftwareTypes.SENET:
            raise UnavailableForSenet
        serializer = self.get_serializer(data={**request.data, 'booking': booking.id})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({})


class CheckBookingsPaymentStatusView(JSONRendererMixin, BookingMixin, GenericAPIView):
    queryset = Booking.objects.all()

    def get(self, request, booking_uuid):
        booking = self.get_object()

        payment_status = "NO_PAYMENT_YET"

        if booking.status == BookingStatuses.EXPIRED:
            payment_status = BookingStatuses.EXPIRED
            return Response({"payment_status": payment_status})

        payment = booking.payments.last()
        if payment:
            payment_status = booking.payment_status
        elif booking.use_cashback:
            payment_status = "CASHBACK_APPROVED"

        return Response({"payment_status": payment_status})


class ComputerSessionFinishView(JSONRendererMixin, BookingMixin, GenericAPIView):
    queryset = Booking.objects.all()

    def post(self, request, booking_uuid):
        booking = self.get_object()
        if booking.club_branch.club.software_type == SoftwareTypes.SENET:
            raise UnavailableForSenet
        if booking.status not in [BookingStatuses.SESSION_STARTED, BookingStatuses.PLAYING]:
            raise BookingStatusIsNotAppropriate

        booking.status = BookingStatuses.COMPLETED
        booking.save(update_fields=['status'])
        if config.INTEGRATIONS_TURNED_ON:
            GizmoEndUserSessionService(
                instance=booking.club_branch,
                user_id=booking.club_user.outer_id
            ).run()
            if booking.status == BookingStatuses.SESSION_STARTED:
                unlock_computers.delay(booking.uuid)
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


class CreateBookingForFreeView(JSONRendererMixin, CreateAPIView):
    queryset = Booking.objects.all()
    serializer_class = CreateBookingForFreeSerializer

    def get_serializer_context(self):
        return {
            'request': self.request,
            'booking_method': 'for_free'
        }
