from django.urls import path

from .views import (
    BookingHistoryView,
    CreateBookingByBalanceView,
    CreateBookingByPaymentView,
    CreateBookingByCardPaymentView
)

urlpatterns = [
    path('', BookingHistoryView.as_view()),
    path('by_balance', CreateBookingByBalanceView.as_view()),
    path('by_payment', CreateBookingByPaymentView.as_view()),
    path('by_card_payment', CreateBookingByCardPaymentView.as_view()),
]
