from django.contrib.auth import get_user_model

from apps.authentication.exceptions import UserNotFound
from apps.bookings import BookingStatuses
from apps.bookings.models import Booking
from apps.clubs.models import ClubBranchUser, ClubComputer
from apps.clubs.services import get_correct_phone
from apps.integrations.gizmo.base import BaseGizmoService
from apps.integrations.gizmo.exceptions import UserDoesNotHavePhoneNumber, GizmoRequestError
from apps.integrations.gizmo.serializers import GizmoUserSaveSerializer

User = get_user_model()


class GizmoGetUsersService(BaseGizmoService):
    endpoint = "/api/users"
    save_serializer = GizmoUserSaveSerializer
    method = "GET"

    def save(self, response):
        if response.get('result') and isinstance(response['result'], list):
            resp_data = response['result']
            for gizmo_user in resp_data:
                if not ClubBranchUser.objects.filter(
                        gizmo_id=gizmo_user['id'],
                        club_branch_id=self.instance.id
                ).exists():
                    try:
                        gizmo_phone = get_correct_phone(gizmo_user['phone'], gizmo_user['mobilePhone'])
                        if gizmo_phone:
                            serializer = self.save_serializer(
                                data={
                                    "gizmo_id": gizmo_user['id'],
                                    "gizmo_phone": gizmo_phone,
                                    "login": gizmo_user['username'],
                                    "club_branch": self.instance.id
                                }
                            )
                            serializer.is_valid(raise_exception=True)
                            serializer.save()
                    except Exception as e:
                        self.log_error(e)


class GizmoGetUserByUsernameService(BaseGizmoService):
    endpoint = "/api/users/{username}/username"
    save_serializer = None
    method = "GET"

    def run_service(self):
        # print("self.kwargs.get('username'): ", self.kwargs.get('username'))
        return self.fetch(path_params={
            "username": self.kwargs.get('username')
        })

    def finalize_response(self, response):
        # print(response)
        gizmo_user = response.get('result')
        if not gizmo_user:
            raise UserNotFound

        gizmo_phone = get_correct_phone(gizmo_user['phone'], gizmo_user['mobilePhone'])
        if not gizmo_phone:
            raise UserDoesNotHavePhoneNumber

        try:
            user = User.objects.filter(mobile_phone=gizmo_phone).first()
            if user:
                user = user.id
            serializer = GizmoUserSaveSerializer(
                data={
                    "gizmo_id": gizmo_user['id'],
                    "gizmo_phone": gizmo_phone,
                    "login": gizmo_user['username'],
                    "club_branch": self.instance.id,
                    "user": user
                }
            )
            serializer.is_valid(raise_exception=True)
            club_user = serializer.save()
            return club_user

        except Exception as e:
            self.log_error(e)


class GizmoGetUserBalanceService(BaseGizmoService):
    endpoint = "/api/users/{user_id}/balance"
    save_serializer = None
    method = "GET"

    def run_service(self):
        return self.fetch(path_params={
            "user_id": self.kwargs.get('user_id')
        })

    def finalize_response(self, response):
        print(response)
        gizmo_user = response.get('result')
        if not gizmo_user:
            raise UserNotFound

        club_user = ClubBranchUser.objects.filter(gizmo_id=gizmo_user["userId"]).first()
        if club_user:
            club_user.balance = gizmo_user['balance']
            club_user.save()

        return gizmo_user['balance']


class GizmoUpdateComputerStateByUserSessionsService(BaseGizmoService):
    """
    Updates computers state and
    returns user gizmo ids with active sessions
    """
    endpoint = "/api/usersessions/activeinfo"
    save_serializer = None
    method = "GET"

    def finalize_response(self, response):
        print(response)
        if response and response.get('result') and isinstance(response['result'], list):
            resp_data = response['result']
            active_users = []
            for user_session in resp_data:
                active_users.append(user_session['userId'])
                computer = ClubComputer.objects.filter(
                    gizmo_id=user_session['hostId'],
                    club_branch_id=self.instance.id
                ).first()
                if computer:
                    computer.is_booked = True
                    computer.save()

            uncompleted_bookings = Booking.objects.filter(status=BookingStatuses.PLAYING)
            for booking in uncompleted_bookings:
                if booking.club_user.gizmo_id not in active_users:
                    booking.status = BookingStatuses.COMPLETED
                    booking.save(update_fields=['status'])

            return active_users


class GizmoStartUserSessionService(BaseGizmoService):
    endpoint = "/api/users/{user_id}/login/{computer_id}"
    save_serializer = None
    method = "POST"

    def run_service(self):
        return self.fetch(path_params={
            "user_id": self.kwargs.get('user_id'),
            "computer_id": self.kwargs.get('computer_id'),
        })

    def finalize_response(self, response):
        print(response)
        if response.get('isError') == True:
            self.log_error(str(response['errors']))
            raise GizmoRequestError


class GizmoEndUserSessionService(BaseGizmoService):
    endpoint = "/api/users/{user_id}/logout"
    save_serializer = None
    method = "POST"

    def run_service(self):
        return self.fetch(path_params={
            "user_id": self.kwargs.get('user_id')
        })

    def finalize_response(self, response):
        if response.get('isError') == True:
            self.log_error(str(response['errors']))
            raise GizmoRequestError
