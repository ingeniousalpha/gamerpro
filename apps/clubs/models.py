from django.db import models

from apps.clubs import SoftwareTypes
from apps.clubs.managers import HallTypesManager
from apps.common.models import TimestampModel
from apps.integrations.models import OuterServiceLogHistory


class HallTypesManagerMixin:
    objects = HallTypesManager()


class ClubUserCashbackManager(models.Manager):
    def get_balance(self, club):
        if c := self.get_queryset().filter(club=club).first():
            return c.cashback_amount
        return None

    def add(self, amount, club):
        if amount == 0:
            raise Exception("Cannot add 0 cashback")

        club_cashback = self.get_queryset().filter(club=club).first()
        club_cashback.cashback_amount += amount
        club_cashback.save()


class Club(models.Model):
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=50, null=True, blank=True)
    description = models.TextField()
    is_bro_chain = models.BooleanField(default=False)
    software_type = models.CharField(choices=SoftwareTypes.choices, null=True, max_length=20)

    class Meta:
        verbose_name = "Клуб"
        verbose_name_plural = "Клубы"

    def __str__(self):
        return self.name

    def get_perk(self, code):
        perk = self.perks.filter(code=code).first()
        if perk:
            return perk.value


class ClubBranchLegalEntity(models.Model):
    name = models.CharField(max_length=256, default="")
    code = models.CharField(max_length=30, default="")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "ИПшка"
        verbose_name_plural = "ИПшки"


class ClubBranch(OuterServiceLogHistory):
    outer_id = models.CharField("Внешний ID точки в системе партнера", null=True, blank=True, max_length=20)
    club = models.ForeignKey(Club, on_delete=models.PROTECT, related_name="branches")
    main_club_branch = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='siblings',
        verbose_name="Основной филиал"
    )
    name = models.CharField(max_length=50)
    trader_name = models.CharField(max_length=256, default="")
    address = models.CharField(max_length=255)
    api_host = models.URLField("Белый IP адрес филиала", default="http://127.0.0.1:8000")
    api_user = models.CharField("Логин для API филиала", max_length=20, null=True)
    api_password = models.CharField("Пароль для API филиала", max_length=20, null=True)
    cashbox_user = models.CharField("Логин для кассы филиала", max_length=20, null=True, blank=True)
    cashbox_password = models.CharField("Пароль для кассы филиала", max_length=20, null=True, blank=True)
    gizmo_payment_method = models.IntegerField(default=2)  # payment method - online payment
    gizmo_points_method = models.IntegerField(default=-4)  # payment method - points payment
    is_active = models.BooleanField(default=False)
    is_ready = models.BooleanField(default=False)
    is_turned_on = models.BooleanField(default=True)
    priority = models.IntegerField(default=0)
    image = models.ImageField(upload_to='images', null=True, blank=True)
    trader = models.ForeignKey(
        ClubBranchLegalEntity,
        on_delete=models.PROTECT,
        related_name="club_branches",
        null=True
    )
    extra_data = models.JSONField(null=True, blank=True)
    city = models.ForeignKey(
        "common.City",
        on_delete=models.SET_NULL,
        related_name="club_branches",
        null=True, blank=True
    )

    class Meta:
        verbose_name = "Филиал Клуба"
        verbose_name_plural = "Филиалы Клубов"
        ordering = ['id']

    def __str__(self):
        return f"{self.club} {self.name}"

    def software_type(self):
        return self.club.software_type


class ClubPerk(models.Model):
    club = models.ForeignKey(
        Club, related_name="perks",
        on_delete=models.SET_NULL,
        null=True, blank=True
    )
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50)
    value = models.IntegerField(default=0)

    class Meta:
        unique_together = ("club", "code")

    def __str__(self):
        return f"{self.club}/{self.code}"


class ClubComputerGroup(models.Model):
    club_branch = models.ForeignKey(ClubBranch, on_delete=models.CASCADE, related_name="computer_groups")
    name = models.CharField(max_length=20)
    outer_id = models.IntegerField(null=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.club_branch} {self.name}"

    class Meta:
        verbose_name = "Зал клубов"
        verbose_name_plural = "Залы клубов"


class ClubComputerLayoutGroup(models.Model):
    club_branch = models.ForeignKey(ClubBranch, on_delete=models.CASCADE, related_name="layout_groups")
    name = models.CharField(max_length=20)
    outer_id = models.IntegerField(null=True, blank=True)
    is_available = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Layout Group"
        verbose_name_plural = "Layout Groups"

    def __str__(self):
        return f"{self.club_branch} {self.name}"


class ClubComputer(models.Model):
    outer_id = models.IntegerField(null=True, db_index=True)
    club_branch = models.ForeignKey(
        ClubBranch,
        on_delete=models.CASCADE,
        related_name="computers",
        db_index=True
    )
    number = models.IntegerField()
    group = models.ForeignKey(
        ClubComputerGroup,
        null=True, on_delete=models.SET_NULL,
        related_name="computers"
    )
    layout_group = models.ForeignKey(
        ClubComputerLayoutGroup,
        null=True, blank=True, on_delete=models.SET_NULL,
        related_name="computers"
    )
    is_active_session = models.BooleanField(default=False)
    is_locked = models. BooleanField(default=False)
    is_broken = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    outer_hostname = models.CharField(max_length=10, null=True, blank=True)

    def __str__(self):
        if self.outer_hostname:
            return self.outer_hostname
        return f"Comp({self.number})"

    class Meta:
        ordering = ['number']
        verbose_name = "Компьютер клуба"
        verbose_name_plural = "Компьютеры клуба"

    @property
    def is_booked(self):
        return self.is_active_session or self.is_locked or self.is_broken


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
    outer_id = models.IntegerField(null=True)
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
    outer_id = models.IntegerField(null=True)
    outer_name = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, null=True, blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0.0)
    price_for_holidays = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Цена праздничного дня"
    )
    use_holiday_price = models.BooleanField(default=False, verbose_name="Использовать цену праздничного дня")
    minutes = models.IntegerField(default=0, null=True, blank=True)
    club = models.ForeignKey(
        Club,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="time_packets"
    )
    packet_group = models.ForeignKey(
        ClubTimePacketGroup,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="packets"
    )
    club_computer_group = models.ForeignKey(
        ClubComputerGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="time_packets"
    )
    priority = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    available_days = models.ManyToManyField(DayModel, related_name="time_packets")
    available_time_start = models.TimeField(null=True, blank=True)
    available_time_end = models.TimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Пакет"
        verbose_name_plural = "Пакеты"

    def __str__(self):
        if self.club_computer_group:
            return f"{self.club_computer_group} ({self.name})"
        if self.packet_group:
            return f"{self.packet_group.computer_group} ({self.name})"
        if self.club:
            return f"{self.club} ({self.name})"

    @property
    def name(self):
        return self.display_name or self.gizmo_name

    @property
    def actual_price(self):
        if self.use_holiday_price and self.price_for_holidays:
            return self.price_for_holidays
        return self.price


class DelayedTimeSetting(TimestampModel):
    club = models.ForeignKey(
        Club,
        on_delete=models.PROTECT,
        related_name="delayed_times"
    )
    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="delayed_time_set",
        null=True, blank=True
    )
    booking = models.ForeignKey(
        "bookings.Booking",
        on_delete=models.CASCADE,
        related_name="delayed_time_set"
    )
    time_packet = models.ForeignKey(
        ClubTimePacket,
        on_delete=models.SET_NULL,
        related_name="delayed_time_set",
        null=True, blank=True
    )


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


class ClubBranchUser(TimestampModel):
    club_branch = models.ForeignKey(ClubBranch, on_delete=models.CASCADE, related_name="users")
    user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE,
        related_name="club_accounts",
        null=True, blank=True
    )
    outer_id = models.IntegerField(null=True, blank=True, db_index=True)
    outer_phone = models.CharField(max_length=12, null=True, db_index=True)
    login = models.CharField(max_length=50)
    first_name = models.CharField(max_length=100, null=True, blank=False)
    balance = models.DecimalField(max_digits=8, decimal_places=2, default=0.0)
    created_by = models.ForeignKey(
        "users.User", on_delete=models.CASCADE,
        related_name="created_club_accounts",
        null=True, blank=True
    )

    @property
    def has_active_booking(self):
        for b in self.bookings.order_by('-created_at'):
            if b.is_active:
                return True
        return False

    @property
    def onevision_payer_id(self):
        if payer := self.user.onevision_payers.filter(trader=self.club_branch.trader).first():
            return payer.payer_id

    @property
    def is_verified(self):
        return bool(self.outer_id)

    def __str__(self):
        if self.outer_phone:
            return f"{self.login}({self.outer_phone})"
        if self.user and self.user.mobile_phone:
            return f"{self.login}({self.user.mobile_phone})"
        return self.login

    class Meta:
        verbose_name = "Юзер в гизмо"
        verbose_name_plural = "Юзеры в гизмо"


class ClubUserCashback(models.Model):
    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="cashbacks",
        null=True, blank=True
    )
    club = models.ForeignKey(
        Club,
        on_delete=models.PROTECT,
        related_name="user_cashbacks"
    )
    cashback_amount = models.IntegerField(default=0)

    objects = ClubUserCashbackManager()


class ClubBranchAdmin(models.Model):
    mobile_phone = models.CharField(max_length=12)
    tg_chat_id = models.CharField(max_length=128, null=True, blank=True)
    tg_username = models.CharField(max_length=128, null=True, blank=True)
    is_active = models.BooleanField(default=False)
    club_branch = models.ForeignKey(
        ClubBranch,
        on_delete=models.CASCADE,
        related_name="telegram_admins",
        null=True, blank=True
    )

    class Meta:
        verbose_name = "Админ в телеге"
        verbose_name_plural = "Админы в телеге"
