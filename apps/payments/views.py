import logging
import urllib
from datetime import datetime

from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.response import Response

from constance import config
from apps.common.mixins import PublicJSONRendererMixin, JSONRendererMixin, PublicAPIMixin
from apps.payments.models import PaymentCard
from apps.payments.services import handle_ov_response
from apps.common.utils import b64_decode
from . import PaymentStatuses
from .serializers import PaymentCardListSerializer, DepositReplenishmentSerializer
from ..bookings import BookingStatuses
from ..bookings.models import Booking
from ..bookings.tasks import gizmo_book_computers, gizmo_bro_add_time_and_set_booking_expiration
from ..clubs.models import ClubBranch

logger = logging.getLogger("onevision")

KASPI_ERROR_CODES = {
    "booking_not_found": 1,
    "booking_already_paid": 2,
    "internal_server_error": 3,
    "booking_already_expired": 4,
}


class OVWebhookHandlerView(PublicJSONRendererMixin, GenericAPIView):

    def post(self, request):
        success = Response(status=status.HTTP_200_OK)
        try:
            webhook_data = b64_decode(urllib.parse.unquote_plus(request.data.get('data')))
            print('OV webhook handled')
            print(webhook_data)
            handle_ov_response(webhook_data)
        except Exception as e:
            logger.error(f"WEBHOOK PAYMENT={webhook_data['transaction_id']} ERROR: {str(e)}")
        return success


class KaspiCallbackHandlerView(PublicAPIMixin, GenericAPIView):
    def get(self, request):
        resp_data = {
            "txn_id": "",
            "result": 0,
            "sum": 0,
            "comment": "",
        }
        try:
            command = request.GET.get('command')
            resp_data["txn_id"] = request.GET.get('txn_id')
            txn_date = request.GET.get('txn_date')
            booking_uuid = request.GET.get('account')
            sum = request.GET.get('sum')
            print("Kaspi webhook handled")
            print(
                f"Command: {command}, txn_id: {resp_data['txn_id']}, txn_date: {txn_date}, "
                f"booking_uuid: {booking_uuid}, sum: {sum}"
            )

            if booking_uuid == "777999":
                resp_data["sum"] = sum
                resp_data["comment"] = "OK"
                return Response(resp_data)

            booking = Booking.objects.filter(uuid=booking_uuid).first()
            payment = booking.payments.last()
            if not booking:
                resp_data["error_msg_code"] = "booking_not_found"
            elif booking.created_at + timezone.timedelta(minutes=config.PAYMENT_EXPIRY_TIME) <= timezone.now():
                resp_data["error_msg_code"] = "booking_already_expired"
                # booking.status = BookingStatuses.EXPIRED
                # booking.save()
            elif booking.payments.exists() and booking.payments.last().status != PaymentStatuses.CREATED:
                # TODO: rewrite
                resp_data["error_msg_code"] = "booking_already_paid"

            if "error_msg_code" in resp_data:
                resp_data["result"] = KASPI_ERROR_CODES.get(resp_data["error_msg_code"])
                return Response(resp_data)

            resp_data["sum"] = "{:.2f}".format(payment.amount)

            if command == "check":
                payment.outer_id = resp_data["txn_id"]
                payment.save(update_fields=['outer_id'])
            elif command == "pay":
                resp_data["prv_txn_id"] = str(payment.uuid)
                resp_data["comment"] = "OK"
                # payment.updated_at = datetime.strptime(txn_date, "%Y%m%d%H%M%S")
                payment.status = PaymentStatuses.PAYMENT_APPROVED
                payment.save(update_fields=["status", "updated_at"])

                if booking.club_branch.club.name.lower() == "bro" and booking.club_user.is_verified:
                    gizmo_bro_add_time_and_set_booking_expiration.delay(booking_uuid)
                elif booking.club_branch.club.name.lower() != "bro":
                    gizmo_book_computers(booking_uuid)

        except ValidationError:
            resp_data["error_msg_code"] = "booking_not_found"
            resp_data["result"] = KASPI_ERROR_CODES.get(resp_data["error_msg_code"])
        except Exception as e:
            print("KaspiCallbackHandlerView internal_server_error: ", str(e))
            resp_data["error_msg_code"] = "internal_server_error"
            resp_data["result"] = KASPI_ERROR_CODES.get(resp_data["error_msg_code"])

        return Response(resp_data)


class PaymentCardListView(JSONRendererMixin, ListAPIView):
    serializer_class = PaymentCardListSerializer
    pagination_class = None

    def get_queryset(self):
        return PaymentCard.objects.filter(
            is_deleted=False,
            user=self.request.user,
            pay_token__isnull=False,
        ).order_by('created_at')


class PaymentCardDeleteView(JSONRendererMixin, GenericAPIView):
    queryset = PaymentCard.objects.all()

    def post(self, request, pk):
        card = self.get_object()
        card.is_deleted = True
        card.save()
        return Response({}, status=status.HTTP_200_OK)


class DepositReplenishmentView(JSONRendererMixin, GenericAPIView):
    serializer_class = DepositReplenishmentSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({})


def ov_payment_succeed_view(request):
    return HttpResponse("")


def ov_payment_failed_view(request):
    return HttpResponse("")
