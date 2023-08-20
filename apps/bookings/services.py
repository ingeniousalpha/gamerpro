from django.utils import timezone

from apps.bookings import BookingStatuses, PlatformTypes
from apps.bookings.models import Booking, BookedComputer
from apps.clubs.models import ClubComputer
from apps.integrations.gizmo.users_services import GizmoUpdateComputerStateByUserSessionsService


def check_user_session(club_user):
    active_users = GizmoUpdateComputerStateByUserSessionsService(instance=club_user.club_branch).run()
    active_session = next((u for u in active_users if u['user_gizmo_id'] == club_user.gizmo_id), None)
    if active_session:
        if not Booking.objects.filter(
                club_user=club_user,
                created_at__gte=timezone.now()-timezone.timedelta(hours=12),
                status__in=[
                    BookingStatuses.ACCEPTED,
                    BookingStatuses.SESSION_STARTED,
                    BookingStatuses.PLAYING,
                ]
        ).exists():
            booking = Booking.objects.create(
                status=BookingStatuses.PLAYING,
                club_branch=club_user.club_branch,
                club_user=club_user,
                platform=PlatformTypes.PHYSICAL
            )
            BookedComputer.objects.create(
                booking=booking,
                computer=ClubComputer.objects.filter(gizmo_id=active_session['computer_gizmo_id'].first())
            )
