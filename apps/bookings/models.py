from django.db import models

from apps.bookings import BookingStatuses
from apps.clubs.models import ClubComputer
from apps.common.models import UUIDModel, TimestampModel


class Booking(UUIDModel, TimestampModel):
    club_branch = models.ForeignKey(
        "clubs.ClubBranch",
        on_delete=models.CASCADE,
        related_name="bookings"
    )
    club_user = models.ForeignKey(
        "clubs.ClubBranchUser",
        on_delete=models.CASCADE,
        related_name="bookings"
    )
    status = models.CharField(
        max_length=20,
        choices=BookingStatuses.choices,
        default=BookingStatuses.IN_PROCESS
    )
    use_balance = models.BooleanField(default=True)
    amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0.0
    )
    payment_card = models.ForeignKey(
        "payments.PaymentCard",
        on_delete=models.SET_NULL,
        related_name="bookings",
        null=True, blank=True
    )
    expiration_date = models.DateTimeField(auto_now=True)


class BookedComputer(models.Model):
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name="computers"
    )
    computer = models.ForeignKey(
        ClubComputer,
        on_delete=models.PROTECT,
    )


class DepositReplenishment(TimestampModel):
    gizmo_id = models.IntegerField(null=True)
    club_branch = models.ForeignKey(
        "clubs.ClubBranch",
        on_delete=models.CASCADE,
        related_name="user_replenishments"
    )
    club_user = models.ForeignKey(
        "clubs.ClubBranchUser",
        on_delete=models.CASCADE,
        related_name="replenishments"
    )
    amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0.0
    )
