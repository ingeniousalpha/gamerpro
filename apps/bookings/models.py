from decimal import Decimal
from django.db import models

from apps.bookings import BookingStatuses, PlatformTypes
from apps.clubs.models import ClubComputer
from apps.common.models import UUIDModel, TimestampModel
from constance import config

from apps.integrations.models import OuterServiceLogHistory
from apps.payments import PaymentStatuses, PAYMENT_STATUSES_MAPPER


class Booking(UUIDModel, TimestampModel, OuterServiceLogHistory):
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
        default=BookingStatuses.ACCEPTED
    )
    use_balance = models.BooleanField(default=False)
    use_cashback = models.BooleanField(default=False)
    for_free = models.BooleanField(default=False)
    platform = models.CharField(
        max_length=256,
        choices=PlatformTypes.choices,
        default=PlatformTypes.WEB
    )
    amount = models.DecimalField(  # amount sent to balance
        max_digits=8,
        decimal_places=2,
        default=0.0
    )
    commission_amount = models.DecimalField(  # our commission
        max_digits=8,
        decimal_places=2,
        default=0.0
    )
    total_amount = models.DecimalField(  # amount user paid
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
    is_cancelled = models.BooleanField(default=False)
    is_starting_session = models.BooleanField(default=False)
    is_time_packet_set = models.BooleanField(default=False)
    time_packet = models.ForeignKey(
        "clubs.ClubTimePacket",
        on_delete=models.SET_NULL,
        related_name="bookings",
        null=True, blank=True
    )

    class Meta:
        verbose_name = "Бронь"
        verbose_name_plural = "Брони"

    @property
    def is_active(self):
        if self.status in [
            BookingStatuses.ACCEPTED,
            BookingStatuses.SESSION_STARTED,
            BookingStatuses.PLAYING
        ]:
            if self.payments.exists() and self.payments.last().status == PaymentStatuses.PAYMENT_APPROVED:
                return True
            elif self.use_cashback:
                return True
        return False

    @staticmethod
    def get_commission_amount(amount):
        # here will be calculations based on amount
        return Decimal(config.GAMER_PRO_COMMISSION)

    @property
    def payment_status(self):
        if self.payments.exists():
            return PAYMENT_STATUSES_MAPPER.get(int(self.payments.last().status))


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

    @property
    def is_active_session(self):
        return self.computer.is_active_session

    @property
    def is_locked(self):
        return self.computer.is_locked


class DepositReplenishment(TimestampModel):
    outer_id = models.IntegerField(null=True)
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
    user_received_amount = models.DecimalField(  # amount sent to balance including cashback_amount
        max_digits=8,
        decimal_places=2,
        default=0.0
    )
    cashback_amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0.0
    )
    commission_amount = models.DecimalField(  # our commission
        max_digits=8,
        decimal_places=2,
        default=0.0
    )
    total_amount = models.DecimalField(  # amount user paid
        max_digits=8,
        decimal_places=2,
        default=0.0
    )
    booking = models.ForeignKey(
        "bookings.Booking",
        on_delete=models.CASCADE,
        related_name="replenishments",
        null=True, blank=True
    )
    payment_card = models.ForeignKey(
        "payments.PaymentCard",
        on_delete=models.CASCADE,
        related_name="replenishments",
        null=True, blank=True
    )
    time_packet = models.ForeignKey(
        "clubs.ClubTimePacket",
        on_delete=models.SET_NULL,
        related_name="replenishments",
        null=True, blank=True
    )
