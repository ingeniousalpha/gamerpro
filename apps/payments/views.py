import logging
import urllib

from django.http import HttpResponse
from rest_framework import status
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.response import Response


from apps.common.mixins import PublicJSONRendererMixin, JSONRendererMixin
from apps.payments.models import PaymentCard
from apps.payments.services import b64_decode, handle_ov_response
from .serializers import PaymentCardListSerializer, SavePaymentSerializer

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


class PaymentCardListView(JSONRendererMixin, ListAPIView):
    serializer_class = PaymentCardListSerializer
    pagination_class = None

    def get_queryset(self):
        return PaymentCard.objects.filter(is_deleted=False, user=self.request.user).order_by('created_at')


class PaymentCardDeleteView(JSONRendererMixin, GenericAPIView):
    queryset = PaymentCard.objects.all()

    def post(self, request, pk):
        card = self.get_object()
        card.is_deleted = True
        card.save()
        return Response({}, status=status.HTTP_200_OK)


def ov_payment_succeed_view(request):
    return HttpResponse("")


def ov_payment_failed_view(request):
    return HttpResponse("")
