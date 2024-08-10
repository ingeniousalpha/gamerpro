from django.db.models import TextChoices

default_app_config = 'apps.clubs.apps.ClubsConfig'


class ClubHallTypes(TextChoices):
    STANDARD = "STANDARD", "Стандарт"
    VIP = "VIP", "ВИП"


class SoftwareTypes(TextChoices):
    SENET = "SENET", "SENET"
    GIZMO = "GIZMO", "GIZMO"
