from rest_framework.generics import CreateAPIView

from apps.bookings.models import Booking
from apps.bookings.serializers import CreateBookingUsingBalanceSerializer, CreateBookingWithPaymentSerializer
from apps.common.mixins import PublicJSONRendererMixin


class CreateBookingUsingBalanceView(PublicJSONRendererMixin, CreateAPIView):
    queryset = Booking.objects.all()
    serializer_class = CreateBookingUsingBalanceSerializer


class CreateBookingWithPaymentView(PublicJSONRendererMixin, CreateAPIView):
    queryset = Booking.objects.all()
    serializer_class = CreateBookingWithPaymentSerializer
