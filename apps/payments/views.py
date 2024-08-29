import logging
import urllib

from django.http import HttpResponse
from rest_framework import status
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.response import Response


from apps.common.mixins import PublicJSONRendererMixin, JSONRendererMixin, PublicAPIMixin
from apps.payments.models import PaymentCard
from apps.payments.services import handle_ov_response
from apps.common.utils import b64_decode
from .serializers import PaymentCardListSerializer, DepositReplenishmentSerializer
from ..clubs.models import ClubBranch

logger = logging.getLogger("onevision")


class OVWebhookHandlerView(PublicJSONRendererMixin, GenericAPIView):

    def post(self, request):
        success = Response(status=status.HTTP_200_OK)
        try:
            webhook_data = b64_decode(urllib.parse.unquote_plus(request.data.get('data')))
            print('This is webhook')
            print(webhook_data)
            handle_ov_response(webhook_data)
        except Exception as e:
            logger.error(f"WEBHOOK PAYMENT={webhook_data['transaction_id']} ERROR: {str(e)}")
        return success


class KaspiCallbackHandlerView(PublicAPIMixin, GenericAPIView):
    def get(self, request):
        try:
            command = request.GET.get('command')
            txn_id = request.GET.get('txn_id')
            txn_date = request.GET.get('txn_date')
            account = request.GET.get('account')
            sum = request.GET.get('sum')
        except Exception as e:
            print("KaspiCallbackHandlerView error: ", str(e))
            return Response({
                "txn_id": txn_id,
                "sum": 500,
                "comment": "",
                "result": 3,
                "error_msg_code": "internal_server_error"
            })
        return Response({
            "txn_id": txn_id,
            "result": 0,
            "sum": 500,
            "comment": "",
        })


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
