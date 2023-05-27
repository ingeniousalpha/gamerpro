from django.urls import path

from .views import CreateBookingUsingBalanceView, CreateBookingWithPaymentView

urlpatterns = [
    path('', CreateBookingUsingBalanceView.as_view()),
    path('payment', CreateBookingWithPaymentView.as_view()),
]
