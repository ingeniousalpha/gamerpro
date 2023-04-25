from django.contrib.auth import get_user_model
from django.db import models

from apps.clubs import ClubHallTypes
from apps.clubs.managers import HallTypesManager

User = get_user_model()


class HallTypesManagerMixin:
    objects = HallTypesManager()


class Club(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField()

    class Meta:
        verbose_name = "Компьютерный Клуб"
        verbose_name_plural = "Компьютерные Клубы"

    def __str__(self):
        return self.name


class ClubBranch(models.Model):
    club = models.ForeignKey(Club, on_delete=models.PROTECT, related_name="branches")
    name = models.CharField(max_length=50)
    address = models.CharField(max_length=255)

    class Meta:
        verbose_name = "Филиал Клуба"
        verbose_name_plural = "Филиалы Клубов"

    def __str__(self):
        return self.name


class ClubComputer(HallTypesManagerMixin, models.Model):
    club_branch = models.ForeignKey(ClubBranch, on_delete=models.CASCADE, related_name="computers")
    number = models.IntegerField()
    hall_type = models.CharField(max_length=20, choices=ClubHallTypes.choices, default=ClubHallTypes.STANDARD)
    is_booked = models.BooleanField(default=False)


class ClubBranchProperty(HallTypesManagerMixin, models.Model):
    club_branch = models.ForeignKey(ClubBranch, on_delete=models.CASCADE, related_name="properties")
    hall_type = models.CharField(max_length=20, choices=ClubHallTypes.choices, default=ClubHallTypes.STANDARD)
    name = models.CharField(max_length=100)


class ClubBranchHardware(HallTypesManagerMixin, models.Model):
    club_branch = models.ForeignKey(ClubBranch, on_delete=models.CASCADE, related_name="hardware")
    hall_type = models.CharField(max_length=20, choices=ClubHallTypes.choices, default=ClubHallTypes.STANDARD)
    name = models.CharField(max_length=100)


class ClubBranchPrice(HallTypesManagerMixin, models.Model):
    club_branch = models.ForeignKey(ClubBranch, on_delete=models.CASCADE, related_name="prices")
    hall_type = models.CharField(max_length=20, choices=ClubHallTypes.choices, default=ClubHallTypes.STANDARD)
    name = models.CharField(max_length=100)
    price = models.IntegerField()


class ClubUserInfo(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="club_accounts")
    club_branch = models.ForeignKey(ClubBranch, on_delete=models.CASCADE, related_name="users")
    login = models.CharField(max_length=50)
    password = models.CharField(max_length=50)
    balance = models.IntegerField()


