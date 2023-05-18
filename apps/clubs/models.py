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
    api_host = models.URLField("Белый IP адрес филиала", default="http://127.0.0.1:8000")
    api_user = models.CharField("Логин для API филиала", max_length=20, null=True)
    api_password = models.CharField("Пароль для API филиала", max_length=20, null=True)
    gizmo_payment_method = models.IntegerField(default=2)
    is_active = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Филиал Клуба"
        verbose_name_plural = "Филиалы Клубов"
        ordering = ['id']

    def __str__(self):
        return f"{self.club} {self.name}"


class ClubComputerGroup(models.Model):
    club_branch = models.ForeignKey(ClubBranch, on_delete=models.CASCADE, related_name="computer_groups")
    name = models.CharField(max_length=20)
    gizmo_id = models.IntegerField(null=True)

    def __str__(self):
        return self.name


class ClubComputer(models.Model):
    club_branch = models.ForeignKey(ClubBranch, on_delete=models.CASCADE, related_name="computers")
    number = models.IntegerField()
    group = models.ForeignKey(ClubComputerGroup, null=True, on_delete=models.SET_NULL, related_name="computers")
    is_booked = models.BooleanField(default=False)
    gizmo_id = models.IntegerField(null=True)
    gizmo_hostname = models.CharField(max_length=10, null=True)

    def __str__(self):
        if self.gizmo_hostname:
            return self.gizmo_hostname
        return f"Comp({self.number})"

    class Meta:
        ordering = ['number']
        verbose_name = "Компьютер клуба"
        verbose_name_plural = "Компьютеры клуба"


class ClubBranchProperty(models.Model):
    club_branch = models.ForeignKey(ClubBranch, on_delete=models.CASCADE, related_name="properties")
    group = models.ForeignKey(ClubComputerGroup, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=100)


class ClubBranchHardware(models.Model):
    club_branch = models.ForeignKey(ClubBranch, on_delete=models.CASCADE, related_name="hardware")
    group = models.ForeignKey(ClubComputerGroup, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=100)


class ClubBranchPrice(models.Model):
    club_branch = models.ForeignKey(ClubBranch, on_delete=models.CASCADE, related_name="prices")
    group = models.ForeignKey(ClubComputerGroup, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=100)
    price = models.IntegerField()


class ClubBranchUser(models.Model):
    club_branch = models.ForeignKey(ClubBranch, on_delete=models.CASCADE, related_name="users")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="club_accounts", null=True, blank=True)
    gizmo_id = models.IntegerField(null=True)
    gizmo_phone = models.CharField(max_length=12, null=True)
    login = models.CharField(max_length=50)
    balance = models.DecimalField(max_digits=8, decimal_places=2, default=0.0)



