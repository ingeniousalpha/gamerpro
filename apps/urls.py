from django.urls import include, path

from apps.common.views import DocumentListView

urlpatterns = [
    # path("common/", include("apps.common.urls")),
    path("auth/", include("apps.authentication.urls")),
    path("clubs/", include("apps.clubs.urls")),
    path("bookings/", include("apps.bookings.urls")),
    path("payments/", include("apps.payments.urls")),
    path("documents", DocumentListView.as_view()),
]


