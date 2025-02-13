from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.clubs.views import (
    ClublistView, ClubBranchlistView, BROClubBranchlistView, ClubBranchDetailView, ClubBranchTimePacketListView,
    ClubUserCashbackView, SenetClubBranchUserRegisterView, SenetClubBranchUserListView, SenetClubBranchUserLoginView,
    SeatingPlanRetrieveUpdateView, ClubBranchUserFeedbackViewSet)

router = DefaultRouter()
router.register(
    r'branches/(?P<club_branch_id>\d+)/feedbacks',
    ClubBranchUserFeedbackViewSet,
    basename="club-branch-feedbacks"
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
    path('branches/<int:pk>/seating/', SeatingPlanRetrieveUpdateView.as_view(), name="seating-plan-update"),
    path('', include(router.urls)),

]
