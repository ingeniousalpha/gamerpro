default_app_config = 'apps.payments.apps.PaymentsConfig'

from django.db.models import TextChoices


class PaymentStatuses(TextChoices):
    CREATED = "0", "Транзакция Создана"
    AUTH = "1", "Захолдированы средства"
    VOID = "2", "Разхолдированы средства"
    PAYMENT_APPROVED = "3", "Оплчено"
    REFUND_APPROVED = "4", "Возвращено"
    IN_PROGRESS = "8", "В обработке"
    FAILED = "99", "Ошибка"


PAYMENT_STATUSES_MAPPER = {
    0: "CREATED",
    1: "AUTH",
    2: "VOID",
    3: "PAYMENT_APPROVED",
    4: "REFUND_APPROVED",
    8: "IN_PROGRESS",
    99: "FAILED"
}
