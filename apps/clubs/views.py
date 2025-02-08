from django.db.models import Q, F, Count, Case, When, BooleanField
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, viewsets, mixins
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView, RetrieveAPIView, GenericAPIView
from rest_framework.response import Response

from apps.authentication.services import validate_password
from apps.clubs import SoftwareTypes
from apps.clubs.exceptions import NeedToInputUserLogin, ClubBranchNotFound
from apps.clubs.models import Club, ClubBranch, ClubTimePacket, ClubUserCashback, ClubBranchUser
from apps.clubs.serializers import (
    ClubListSerializer, ClubBranchListSerializer, ClubBranchDetailSerializer, ClubTimePacketListSerializer,
    ClubUserCashbackSerializer, ShortClubUserSerializer, ClubListV2Serializer, ClubBranchListV2Serializer
, SeatingPlanSerializer,
)
from apps.clubs.tasks import _sync_club_branch_computers
from apps.common.exceptions import InvalidInputData
from apps.common.mixins import PublicJSONRendererMixin, JSONRendererMixin, PrivateJSONRendererMixin
from apps.common.pagination import ClubsPagination
from apps.integrations.senet.exceptions import SenetIntegrationError
from apps.integrations.senet.users_services import SenetCreateUserService, SenetSearchUserService


class ClublistView(PublicJSONRendererMixin, ListAPIView):
    queryset = Club.objects.all()
    serializer_class = ClubListSerializer


class ClubListV2View(PublicJSONRendererMixin, ListAPIView):
    queryset = Club.objects.all()
    serializer_class = ClubListV2Serializer
    pagination_class = ClubsPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        return (
            queryset
            .annotate(
                branch_count=Count('branches', filter=(Q(branches__is_active=True) & Q(branches__is_turned_on=True))),
                is_chain=Case(
                    When(branch_count__gt=1, then=True),
                    default=False,
                    output_field=BooleanField()
                )
            )
            .filter(branch_count__gt=0)
            .order_by('id')
        )


class ClubBranchListV2View(PublicJSONRendererMixin, ListAPIView):
    queryset = ClubBranch.objects.all()
    serializer_class = ClubBranchListV2Serializer
    pagination_class = ClubsPagination

    def get_object(self):
        return get_object_or_404(Club, pk=self.kwargs.get('pk'))

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(club=self.get_object())


class ClubBranchlistView(PublicJSONRendererMixin, ListAPIView):
    pagination_class = ClubsPagination
    queryset = (ClubBranch.objects.filter(is_active=True, is_turned_on=True)
                .filter(club__is_bro_chain=False)
                .order_by('-priority'))
    serializer_class = ClubBranchListSerializer

    def get_queryset(self):
        if self.request.GET.get('city'):
            return self.queryset.filter(Q(city=self.request.GET.get('city')) & Q(city__is_active=True))
        return self.queryset


class BROClubBranchlistView(PublicJSONRendererMixin, ListAPIView):
    pagination_class = ClubsPagination
    queryset = (ClubBranch.objects.filter(is_active=True, is_turned_on=True)
                .filter(club__is_bro_chain=True)
                .order_by('-priority'))
    serializer_class = ClubBranchListSerializer

    def get_queryset(self):
        if self.request.GET.get('city'):
            return self.queryset.filter(Q(city=self.request.GET.get('city')) & Q(city__is_active=True))
        return self.queryset


class ClubBranchDetailView(PublicJSONRendererMixin, RetrieveAPIView):
    queryset = ClubBranch.objects.all()
    serializer_class = ClubBranchDetailSerializer

    def retrieve(self, request, *args, **kwargs):
        _sync_club_branch_computers(self.get_object())
        return super().retrieve(request, *args, **kwargs)


class ClubBranchTimePacketListView(JSONRendererMixin, ListAPIView):
    queryset = ClubTimePacket.objects.all()
    serializer_class = ClubTimePacketListSerializer
    pagination_class = None

    def get_queryset(self):
        club_branch = (
            ClubBranch.objects
            .filter(id=self.kwargs.get('pk'))
            .select_related('club')
            .first()
        )
        if not club_branch:
            raise ClubBranchNotFound
        queryset = super().get_queryset().filter(
            is_active=True,
            available_days__number=timezone.now().astimezone().weekday() + 1
        )
        if club_branch.club.software_type == SoftwareTypes.SENET:
            queryset = queryset.filter(club=club_branch.club)
        else:
            queryset = queryset.filter(club_computer_group_id=self.kwargs.get('hall_id'))
        return queryset.filter(
            (Q(available_time_start__lte=timezone.now().astimezone().time()) & Q(
                available_time_end__gte=timezone.now().astimezone().time())) |
            (Q(available_time_start__gte=F('available_time_end')) & (
                    Q(available_time_end__gte=timezone.now().astimezone().time()) | Q(
                available_time_start__lte=timezone.now().astimezone().time()))
             )
        ).order_by('priority')


class ClubUserCashbackView(JSONRendererMixin, RetrieveAPIView):
    queryset = ClubUserCashback.objects.all()
    serializer_class = ClubUserCashbackSerializer

    def get_object(self):
        obj = super().get_queryset().filter(
            club_id=self.kwargs.get('pk'),
            user=self.request.user
        ).first()
        if not obj:
            obj = ClubUserCashback.objects.create(
                club_id=self.kwargs.get('pk'),
                user=self.request.user,
            )
        return obj


class SenetClubBranchUserRegisterView(PrivateJSONRendererMixin, GenericAPIView):
    queryset = ClubBranchUser.objects.all()
    serializer_class = None

    def get_object(self):
        return get_object_or_404(ClubBranch, pk=self.kwargs.get('pk'))

    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        if not isinstance(username, str) or not username:
            raise NeedToInputUserLogin
        password = request.data.get('password')
        validate_password(password)
        club_branch = self.get_object()
        if club_branch.main_club_branch:
            club_branch = club_branch.main_club_branch
        if ClubBranchUser.objects.filter(club_branch=club_branch, user=request.user).exists():
            raise SenetIntegrationError(
                "У Вас уже есть аккаунт в выбранном филиале клуба. "
                "Пожалуйста, обратитесь к администратору или в службу поддержки."
            )
        response = SenetCreateUserService(
            instance=club_branch,
            username=username,
            password=password,
            mobile_phone=str(request.user.mobile_phone),
            email=request.user.email
        ).run()
        ClubBranchUser.objects.create(
            club_branch=club_branch,
            user=request.user,
            outer_id=response.get('account_id'),
            outer_phone=response['dic_user'].get('phone'),
            login=response['dic_user'].get('login'),
            balance=response.get('account_amount')
        )
        return Response({}, status=status.HTTP_201_CREATED)


class SenetClubBranchUserListView(PrivateJSONRendererMixin, GenericAPIView):
    queryset = ClubBranchUser.objects.all()
    serializer_class = None

    def get_object(self):
        return get_object_or_404(ClubBranch, pk=self.kwargs.get('pk'))

    def get(self, request, *args, **kwargs):
        exception_message = "{} Пожалуйста, обратитесь к администратору или в службу поддержки."
        club_branch = self.get_object()
        if club_branch.main_club_branch:
            club_branch = club_branch.main_club_branch
        if ClubBranchUser.objects.filter(club_branch=club_branch, user=request.user).exists():
            raise SenetIntegrationError(
                exception_message.format("Вы уже авторизованы в выбранном филиале клуба.")
            )
        response = SenetSearchUserService(instance=club_branch, phone_number=request.user.mobile_phone_without_code).run()
        club_branch_users = []
        for senet_account in response:
            club_branch_user = (
                ClubBranchUser.objects
                .filter(club_branch=club_branch, login=senet_account["dic_user"]["login"])
                .first()
            )
            if not club_branch_user:
                club_branch_user = ClubBranchUser.objects.create(
                    club_branch=club_branch,
                    outer_id=senet_account.get('account_id'),
                    outer_phone=senet_account['dic_user'].get('phone'),
                    login=senet_account['dic_user'].get('login'),
                    balance=senet_account.get('account_amount')
                )
            if club_branch_user.user is None:
                club_branch_users.append(club_branch_user)
        if not club_branch_users:
            raise SenetIntegrationError(
                exception_message.format("Аккаунт закреплен за другим пользователем.")
            )
        return Response(ShortClubUserSerializer(club_branch_users, many=True).data, status=status.HTTP_200_OK)


class SenetClubBranchUserLoginView(PrivateJSONRendererMixin, GenericAPIView):
    queryset = ClubBranchUser.objects.all()
    serializer_class = None

    def get_object(self):
        return get_object_or_404(ClubBranch, pk=self.kwargs.get('pk'))

    def post(self, request, *args, **kwargs):
        exception_message = "{} Пожалуйста, обратитесь к администратору или в службу поддержки."
        club_branch = self.get_object()
        if club_branch.main_club_branch:
            club_branch = club_branch.main_club_branch
        if ClubBranchUser.objects.filter(club_branch=club_branch, user=request.user).exists():
            raise SenetIntegrationError(
                exception_message.format("Вы уже авторизованы в выбранном филиале клуба.")
            )
        club_branch_user = ClubBranchUser.objects.filter(id=request.data.get('account_id')).first()
        if not club_branch_user:
            raise InvalidInputData
        if club_branch_user.user:
            if club_branch_user.user == request.user:
                return Response({}, status=status.HTTP_200_OK)
            else:
                raise SenetIntegrationError(
                    exception_message.format("Аккаунт закреплен за другим пользователем.")
                )
        club_branch_user.user = request.user
        club_branch_user.save(update_fields=['user', 'first_name', 'updated_at'])
        if request.user.name:
            club_branch_user.first_name = request.user.name
            club_branch_user.save(update_fields=['first_name'])
        return Response({}, status=status.HTTP_200_OK)


class SeatingPlanViewSet(viewsets.ModelViewSet):
    serializer_class = SeatingPlanSerializer

    def get_queryset(self):
        branch_id = self.kwargs.get("pk")  # Используем `pk` из URL
        if branch_id:
            return ClubBranch.objects.filter(id=branch_id)
        return ClubBranch.objects.none()

    def get_object(self):
        branch_id = self.kwargs.get("pk")
        branch = ClubBranch.objects.filter(id=branch_id).first()
        if not branch:
            raise NotFound("Филиал не найден")
        return branch

    def create(self, request, *args, **kwargs):
        branch = self.get_object()
        serializer = self.get_serializer(branch, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        branch = self.get_object()
        return Response({"seating_plan": branch.seating_plan or []}, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        branch = self.get_object()
        serializer = self.get_serializer(branch, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        branch = self.get_object()
        branch.seating_plan = None
        branch.save(update_fields=["seating_plan"])
        return Response({"message": "Рассадка удалена"}, status=status.HTTP_204_NO_CONTENT)