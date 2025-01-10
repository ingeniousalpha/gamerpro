from django.urls import path

from apps.clubs.views import ClubListV2View, ClubBranchListV2View

urlpatterns = [
    path('', ClubListV2View.as_view()),
    path('<int:pk>/branches', ClubBranchListV2View.as_view()),
]
