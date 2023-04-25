from django.urls import path

from apps.clubs.views import ClublistView, ClubBranchlistView, ClubBranchDetailView

urlpatterns = [
    path('', ClublistView.as_view()),
    path('branches', ClubBranchlistView.as_view()),
    path('branches/<int:pk>', ClubBranchDetailView.as_view()),
]
