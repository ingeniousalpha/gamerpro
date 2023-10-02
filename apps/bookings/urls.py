from django.urls import path

from .views import (
    BookingHistoryView,
    CreateBookingByBalanceView,
    CreateBookingByPaymentView,
    CreateBookingByCardPaymentView,
    CancelBookingView,
    UnlockBookedComputersView,
    BookingProlongView,
    BookingDetailView,
    CreateBookingByTimePacketPaymentView,
    CreateBookingByTimePacketCardPaymentView
)

urlpatterns = [
    path('', BookingHistoryView.as_view()),
    path('<uuid:booking_uuid>', BookingDetailView.as_view()),
    path('by_balance', CreateBookingByBalanceView.as_view()),
    path('by_payment', CreateBookingByPaymentView.as_view()),
    path('by_card_payment', CreateBookingByCardPaymentView.as_view()),
    path('by_time_packet_payment', CreateBookingByTimePacketPaymentView.as_view()),
    path('by_time_packet_card_payment', CreateBookingByTimePacketCardPaymentView.as_view()),
    path('<uuid:booking_uuid>/cancel', CancelBookingView.as_view()),
    path('<uuid:booking_uuid>/unlock', UnlockBookedComputersView.as_view()),
    path('<uuid:booking_uuid>/prolong', BookingProlongView.as_view()),
]
