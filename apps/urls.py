from django.urls import include, path

from apps.common.views import DocumentListView, DocumentPrivacyPolicyView

urlpatterns = [
    # path("common/", include("apps.common.urls")),
    path("auth/", include("apps.authentication.urls")),
    path("clubs/", include("apps.clubs.urls")),
    path("bookings/", include("apps.bookings.urls")),
    path("payments/", include("apps.payments.urls")),
    path("notifications/", include("apps.notifications.urls")),
    path("documents", DocumentListView.as_view()),
    path("documents/privacy_policy", DocumentPrivacyPolicyView.as_view()),
]


