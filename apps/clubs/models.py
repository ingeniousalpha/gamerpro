from django.db import models
from apps.clubs.managers import HallTypesManager


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
    image = models.ImageField(upload_to='images', null=True, blank=True)

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
    club_branch = models.ForeignKey(
        ClubBranch,
        on_delete=models.CASCADE,
        related_name="computers",
        db_index=True
    )
    number = models.IntegerField()
    group = models.ForeignKey(ClubComputerGroup, null=True, on_delete=models.SET_NULL, related_name="computers")
    is_active_session = models.BooleanField(default=False)
    is_locked = models. BooleanField(default=False)
    gizmo_id = models.IntegerField(null=True, db_index=True)
    gizmo_hostname = models.CharField(max_length=10, null=True)

    def __str__(self):
        if self.gizmo_hostname:
            return self.gizmo_hostname
        return f"Comp({self.number})"

    class Meta:
        ordering = ['number']
        verbose_name = "Компьютер клуба"
        verbose_name_plural = "Компьютеры клуба"

    @property
    def is_booked(self):
        return self.is_active_session or self.is_locked


class DayModel(models.Model):
    name = models.CharField(max_length=15)
    number = models.IntegerField(default=1)

    class Meta:
        ordering = ['number']
        verbose_name = "День"
        verbose_name_plural = "Дни"

    def __str__(self):
        return self.name


class ClubTimePacketGroup(models.Model):
    gizmo_id = models.IntegerField(null=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    club_branch = models.ForeignKey(
        ClubBranch, on_delete=models.CASCADE,
        related_name="packet_groups"
    )
    computer_group = models.OneToOneField(
        ClubComputerGroup,
        related_name="packet_group",
        null=True, blank=True,
        on_delete=models.SET_NULL
    )

    class Meta:
        verbose_name = "Группа Пакетов"
        verbose_name_plural = "Группы Пакетов"

    def __str__(self):
        return self.name


class ClubTimePacket(models.Model):
    gizmo_id = models.IntegerField(null=True)
    gizmo_name = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, null=True, blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0.0)
    minutes = models.IntegerField(default=0)
    packet_group = models.ForeignKey(
        ClubTimePacketGroup,
        on_delete=models.CASCADE,
        related_name="packets"
    )
    priority = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    available_days = models.ManyToManyField(
        DayModel, null=True, blank=True,
        related_name="time_packets",
    )
    available_time_start = models.TimeField(null=True, blank=True)
    available_time_end = models.TimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Пакет"
        verbose_name_plural = "Пакеты"

    def __str__(self):
        return f"{self.packet_group}({self.name})"

    @property
    def name(self):
        return self.display_name or self.gizmo_name


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
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="club_accounts", null=True, blank=True)
    gizmo_id = models.IntegerField(null=True, db_index=True)
    gizmo_phone = models.CharField(max_length=12, null=True, db_index=True)
    login = models.CharField(max_length=50)
    balance = models.DecimalField(max_digits=8, decimal_places=2, default=0.0)

    @property
    def has_active_booking(self):
        for b in self.bookings.order_by('-created_at'):
            if b.is_active:
                return True
        return False
