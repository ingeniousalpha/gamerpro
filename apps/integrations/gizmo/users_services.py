import urllib
from django.contrib.auth import get_user_model

from apps.authentication.exceptions import UserNotFound
from apps.bookings import BookingStatuses
from apps.bookings.models import Booking
from apps.clubs.models import ClubBranchUser, ClubComputer
from apps.clubs.services import get_correct_phone
from apps.integrations.gizmo.base import BaseGizmoService
from apps.integrations.gizmo.exceptions import UserDoesNotHavePhoneNumber, GizmoRequestError, \
    GizmoLoginAlreadyExistsError
from apps.integrations.gizmo.serializers import GizmoUserSaveSerializer

User = get_user_model()


class GizmoGetUsersService(BaseGizmoService):
    endpoint = "/api/users"
    save_serializer = GizmoUserSaveSerializer
    method = "GET"

    def save(self, response):
        if response.get('result') and isinstance(response['result'], list):
            resp_data = response['result']
            existed_ids = list(ClubBranchUser.objects.filter(club_branch=self.instance).values_list('gizmo_id', flat=True))
            non_existent_users = list(filter(lambda i: i['id'] not in existed_ids, resp_data))

            for gizmo_user in non_existent_users:
                try:
                    gizmo_phone = get_correct_phone(gizmo_user['phone'], gizmo_user['mobilePhone'])
                    serializer = self.save_serializer(
                        data={
                            "gizmo_id": gizmo_user['id'],
                            "gizmo_phone": gizmo_phone,
                            "login": gizmo_user['username'],
                            "first_name": gizmo_user['firstName'],
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
            existing_club_user = ClubBranchUser.objects.filter(
                club_branch_id=self.instance.id, login=gizmo_user['username']
            ).first()
            serializer = GizmoUserSaveSerializer(
                instance=existing_club_user,
                data={
                    "gizmo_id": gizmo_user['id'],
                    "gizmo_phone": gizmo_phone,
                    "login": gizmo_user['username'],
                    "first_name": gizmo_user['firstName'],
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
        gizmo_user = (response or {}).get('result')
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
        from apps.bookings.tasks import send_push_about_booking_status
        active_users = []

        if response and isinstance(response['result'], list):
            resp_data = response['result']

            if len(resp_data) > 0:
                ClubComputer.objects.filter(
                    gizmo_id__in=[r['hostId'] for r in resp_data],
                    club_branch_id=self.instance.id,
                    is_active_session=False
                ).update(is_active_session=True)

            # when resp_data is [], then it updates all computers
            ClubComputer.objects.filter(club_branch_id=self.instance.id)\
                .exclude(gizmo_id__in=[r['hostId'] for r in resp_data],)\
                .filter(is_active_session=True)\
                .update(is_active_session=False)

            for user_session in resp_data:
                active_users.append({
                    "user_gizmo_id": user_session['userId'],
                    "computer_gizmo_id": user_session['hostId']
                })

            # Bookings where:
            # 1 user played and logged out from computer
            # 2 session started and user didn't cancel and admin logged out the user from admin panel
            uncompleted_bookings = Booking.objects.filter(
                is_starting_session=False,
                status__in=[BookingStatuses.PLAYING, BookingStatuses.SESSION_STARTED],
                club_branch_id=self.instance.id,
            )
            active_users_ids = [u['user_gizmo_id'] for u in active_users]
            for booking in uncompleted_bookings:
                if booking.club_user.gizmo_id not in active_users_ids:
                    booking.status = BookingStatuses.COMPLETED
                    booking.save(update_fields=['status'])
                    send_push_about_booking_status(booking.uuid, BookingStatuses.COMPLETED)

            # Bookings where computer is turning on...
            starting_bookings = Booking.objects.filter(club_branch_id=self.instance.id, is_starting_session=True)
            for booking in starting_bookings:
                if booking.club_user.gizmo_id in active_users_ids:
                    booking.is_starting_session = False
                    booking.save(update_fields=['is_starting_session'])

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
        # print(response)
        if response.get('isError') == True:
            self.log_error(str(response['errors']))
            raise GizmoRequestError
        else:
            self.instance.is_starting_session = True
            self.instance.save()


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


class GizmoCreateUserService(BaseGizmoService):
    endpoint = "/api/users?Username={login}&UserGroupId=1&Phone={mobile_phone}&FirstName={first_name}"
    method = "PUT"
    save_serializer = None

    def run_service(self):
        return self.fetch(path_params={
            "login": urllib.parse.quote_plus(self.kwargs.get('login')),
            "first_name": urllib.parse.quote_plus(self.kwargs.get('first_name', '')),
            "mobile_phone": urllib.parse.quote_plus(self.kwargs.get('mobile_phone')),
        })

    def finalize_response(self, response):
        print(response)
        if response.get('isError') == True:
            self.log_error(str(response['errors']))
            if response.get('errorCodeTypeReadable') == "NonUniqueEntityValue":
                raise GizmoLoginAlreadyExistsError
            raise GizmoRequestError

        return response.get('result')  # new user gizmo id
