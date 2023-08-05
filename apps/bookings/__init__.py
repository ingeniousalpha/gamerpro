from django.db.models import TextChoices

default_app_config = 'apps.bookings.apps.BookingsConfig'


class BookingStatuses(TextChoices):
    ACCEPTED = "ACCEPTED", "Бронь принята"
    PLAYING = "PLAYING", "Юзер играет"
    COMPLETED = "COMPLETED", ""
    CANCELLED = "CANCELLED", "Отменено"
