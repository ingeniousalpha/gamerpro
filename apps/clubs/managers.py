from django.db.models import Manager, QuerySet

from apps.clubs import ClubHallTypes


class HallTypesManager(Manager):
    def standard(self):
        return self.get_queryset().filter(hall_type=ClubHallTypes.STANDARD)

    def vip(self):
        return self.get_queryset().filter(hall_type=ClubHallTypes.VIP)
