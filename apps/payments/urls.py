from django.urls import path

from .views import (
    OVWebhookHandlerView,
    PaymentCardListView,
    PaymentCardDeleteView,
    ov_payment_succeed_view,
    ov_payment_failed_view
)

urlpatterns = [
    path('webhook', OVWebhookHandlerView.as_view()),
    path('cards', PaymentCardListView.as_view()),
    path('cards/<int:pk>/delete', PaymentCardDeleteView.as_view()),

    path('success', ov_payment_succeed_view),
    path('fail', ov_payment_failed_view),
]
