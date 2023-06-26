from django.db import models
from django.db.transaction import atomic

from apps.common.models import UUIDModel, TimestampModel
from apps.payments import PaymentStatuses


class PaymentCard(TimestampModel):
    pay_token = models.CharField(
        "Токен карты в платежной системе",
        null=True, blank=True,
        max_length=255
    )
    user = models.ForeignKey(
        "users.User",
        related_name="payment_cards",
        null=True, blank=True,
        on_delete=models.PROTECT
    )
    is_current = models.BooleanField(default=False)
    card_type = models.CharField(
        max_length=256,
        null=True, blank=True
    )
    first_numbers = models.CharField(
        max_length=6,
        null=True, blank=True
    )
    last_numbers = models.CharField(
        max_length=6,
        null=True, blank=True
    )
    is_deleted = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Платежная карта"
        verbose_name_plural = "Платежные карты"

    def __str__(self):
        return self.masked_number

    @property
    def masked_number(self):
        if self.last_numbers:
            return f"**** {self.last_numbers[-4:]}"
        return f"Карта #{self.id}"


class Payment(UUIDModel, TimestampModel):
    outer_id = models.CharField(
        "ID в платежной системе",
        unique=True,
        max_length=16
    )
    status = models.CharField(
        max_length=20,
        choices=PaymentStatuses.choices,
        default=PaymentStatuses.CREATED
    )
    status_reason = models.CharField(max_length=255, null=True, blank=True)
    amount = models.DecimalField(
        "Сумма заказа",
        max_digits=8,
        decimal_places=2
    )
    commission_amount = models.DecimalField(
        "Сумма коммиссии",
        max_digits=8,
        decimal_places=2,
        default=0.0
    )
    card = models.ForeignKey(
        PaymentCard,
        on_delete=models.SET_NULL,
        related_name="payments",
        null=True, blank=True
    )
    currency = models.CharField("Валюта", max_length=3)
    booking = models.OneToOneField(
        "bookings.Booking",
        on_delete=models.CASCADE,
        related_name="payment"
    )
    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="payments"
    )

    class Meta:
        verbose_name = "Платеж"
        verbose_name_plural = "Платежи"

    @atomic
    def change_status(self, status, status_reason=None):
        if self.status == status:
            return

        self.status = status
        self.status_reason = status_reason
        self.save(update_fields=['status', 'status_reason'])
        self.status_transitions.create(status=status, status_reason=status_reason)

    def move_to_in_progress(self):
        self.change_status(PaymentStatuses.IN_PROGRESS)

    def move_to_approved(self):
        self.change_status(PaymentStatuses.PAYMENT_APPROVED)

    def move_to_failed(self, reason):
        self.change_status(PaymentStatuses.FAILED, reason)


class PaymentStatusTransition(TimestampModel):
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name="status_transitions",
    )
    status = models.CharField(
        choices=PaymentStatuses.choices,
        default=PaymentStatuses.CREATED,
        max_length=256,
    )
    status_reason = models.TextField(
        "Причина присвоения статуса",
        null=True, blank=True
    )

    class Meta:
        ordering = ("created_at",)


class PaymentWebhook(TimestampModel):
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name="webhook_history",
        null=True, blank=True
    )
    transaction_id = models.CharField(
        "ID в платежной системе",
        max_length=16
    )
    booking_uuid = models.CharField(
        "ID в платежной системе",
        null=True, blank=True,
        max_length=255,
    )
    data = models.JSONField("Данные")
