from django.urls import include, path

from apps.common.views import (
    DocumentListView,
    DocumentPrivacyPolicyView,
    DocumentPublicOfferView,
    DocumentPaymentPolicyView, BroAppVersionsView, LobbyAppVersionsView,
    CitiesListView,
)

urlpatterns = [
    # path("common/", include("apps.common.urls")),
    path("auth/", include("apps.authentication.urls")),
    path("users/", include("apps.users.urls")),
    path("clubs/", include("apps.clubs.urls")),
    path("v2/clubs/", include("apps.clubs.urls_v2")),
    path("bookings/", include("apps.bookings.urls")),
    path("payments/", include("apps.payments.urls")),
    path("notifications/", include("apps.notifications.urls")),
    path("documents", DocumentListView.as_view()),
    path("documents/privacy_policy", DocumentPrivacyPolicyView.as_view()),
    path("documents/payment_policy", DocumentPaymentPolicyView.as_view()),
    path("documents/public_offer", DocumentPublicOfferView.as_view()),
    path("cities", CitiesListView.as_view()),
    path("app_versions/bro", BroAppVersionsView.as_view()),
    path("app_versions/lobby", LobbyAppVersionsView.as_view()),
]


