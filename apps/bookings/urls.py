from django.urls import path

from .views import CreateBookingUsingBalanceView

urlpatterns = [
    path('', CreateBookingUsingBalanceView.as_view()),
    # path('payment', ClubBranchlistView.as_view()),
]
