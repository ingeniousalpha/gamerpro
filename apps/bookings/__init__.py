from django.db.models import TextChoices

default_app_config = 'apps.bookings.apps.BookingsConfig'


class BookingStatuses(TextChoices):
    IN_PROCESS = "IN_PROCESS", "В обработке"
    DECLINED = "DECLINED", "Отклонено"
    CANCELLED = "CANCELLED", "Отменено"
    ACCEPTED = "ACCEPTED", "Принято"
