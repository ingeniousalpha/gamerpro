from django.db.models import TextChoices

default_app_config = 'apps.bookings.apps.BookingsConfig'


class BookingStatuses(TextChoices):
    ACCEPTED = "ACCEPTED", "Бронь принята"
    SESSION_STARTED = "SESSION_STARTED", "Тарификация началась"  # юзер еще не сел играть
    PLAYING = "PLAYING", "Юзер играет"  # юзер сел играть
    COMPLETED = "COMPLETED", "Зевершено"
    CANCELLED = "CANCELLED", "Отменено"
    EXPIRED = "EXPIRED", "Истекло"


class PlatformTypes(TextChoices):
    WEB = "WEB", "WEB"
    PHYSICAL = "PHYSICAL", "PHYSICAL"
