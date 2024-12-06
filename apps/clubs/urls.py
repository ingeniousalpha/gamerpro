from django.urls import path

from apps.clubs.views import (
    ClublistView, ClubBranchlistView, BROClubBranchlistView, ClubBranchDetailView, ClubBranchTimePacketListView,
    ClubUserCashbackView, SenetClubBranchUserRegisterView, SenetClubBranchUserListView, SenetClubBranchUserLoginView
)

urlpatterns = [
    path('', ClublistView.as_view()),
    path('<int:pk>/cashback', ClubUserCashbackView.as_view()),
    path('branches', ClubBranchlistView.as_view()),
    path('branches/bro', BROClubBranchlistView.as_view()),
    path('branches/<int:pk>', ClubBranchDetailView.as_view()),
    path('branches/<int:pk>/register/', SenetClubBranchUserRegisterView.as_view()),
    path('branches/<int:pk>/accounts/', SenetClubBranchUserListView.as_view()),
    path('branches/<int:pk>/login/', SenetClubBranchUserLoginView.as_view()),
    path('branches/<int:pk>/time_packets/<int:hall_id>', ClubBranchTimePacketListView.as_view()),
]
