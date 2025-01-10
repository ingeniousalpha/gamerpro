import uuid as uuid_lib
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _  # noqa
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from phonenumber_field.modelfields import PhoneNumberField

from .managers import UserManager
from apps.bookings.models import Booking
from ..clubs import SoftwareTypes
from ..clubs.models import ClubPerk
from ..common.models import TimestampModel


class User(PermissionsMixin, AbstractBaseUser):

    class Meta:
        verbose_name = _("Учетная запись")
        verbose_name_plural = _("Учетная запись")

    uuid = models.UUIDField("UUID пользователя", default=uuid_lib.uuid4, unique=True)
    email = models.EmailField("Почта", max_length=40, unique=True, null=True, blank=True)
    name = models.CharField("Имя", max_length=256, null=True, blank=True)
    last_otp = models.CharField("Последний успешный OTP", max_length=4, null=True, blank=True)
    mobile_phone = PhoneNumberField("Моб. телефон", blank=True, null=True)
    secret_key = models.UUIDField("Секретный ключ", default=uuid_lib.uuid4, unique=True)
    club_branches = models.ManyToManyField("clubs.ClubBranch", blank=True, related_name="admins")

    favorite_clubs = models.ManyToManyField("clubs.Club", blank=True, verbose_name='Любимые клубы')
    favorite_club_branches = models.ManyToManyField("clubs.ClubBranch", blank=True, verbose_name='Любимые филиалы клубов')

    is_active = models.BooleanField("Активный", default=True)
    is_staff = models.BooleanField("Сотрудник", default=False)
    is_email_confirmed = models.BooleanField("Почта подтверждена", default=False)
    is_mobile_phone_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(_("Создан"), default=timezone.now)
    updated_at = models.DateTimeField(_("Обновлен"), auto_now=True)

    USERNAME_FIELD = "email"
    objects = UserManager()

    def __str__(self):
        return str(self.mobile_phone or self.email)

    @property
    def has_bookings(self):
        return Booking.objects.filter(club_user__user=self).exists()

    def is_used_perk(self, code):
        return self.perks.filter(perk__code=code).exists()

    def use_perk(self, club, code):
        club_perk = ClubPerk.objects.filter(club=club, code=code).first()
        if club_perk:
            self.perks.add(UserPerk(perk=club_perk), bulk=False)
        else:
            print(f'There is no such perk: {club}, {code}')

    # @property
    # def username(self):
    #     if self.mobile_phone:
    #         return str(self.mobile_phone)
    #     return self.email

    def set_current_card(self, card: 'PaymentCard'):
        self.payment_cards.exclude(id=card.id).update(is_current=False)
        self.payment_cards.filter(id=card.id).update(is_current=True)

    def has_perm(self, perm, obj=None):
        if not self.is_active:
            return False
        if self.is_superuser:
            return True
        return perm in self.get_all_permissions(obj)

    def has_module_perms(self, app_label):
        if self.is_superuser:
            return True
        return self.is_active and any(
            perm[: perm.index(".")] == app_label for perm in self.get_all_permissions()
        )

    # def get_username(self):
    #     return self.mobile_phone

    def set_password(self, raw_password):
        super(User, self).set_password(raw_password)

    def set_active(self):
        self.is_active = True
        self.is_email_confirmed = True
        self.save(update_fields=['is_active', 'is_email_confirmed'])

    def get_is_active(self):
        if self.created_at + timezone.timedelta(days=1) > timezone.now():
            return True
        return self.is_active

    def get_club_account(self, club_branch):
        software_type = club_branch.club.software_type
        if software_type == SoftwareTypes.GIZMO:
            return self.club_accounts.filter(club_branch=club_branch).first()
        elif software_type == SoftwareTypes.SENET:
            return self.club_accounts.filter(club_branch=(club_branch.main_club_branch or club_branch)).first()

    @property
    def mobile_phone_without_code(self):
        phone_number = str(self.mobile_phone)
        phone_number = phone_number[2:] if phone_number[0] == "+" else phone_number[1:]
        return phone_number


class UserOneVisionPayer(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="onevision_payers",
        null=True, blank=True
    )
    trader = models.ForeignKey(
        "clubs.ClubBranchLegalEntity",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="onevision_payers",
    )
    payer_id = models.CharField(
        "ID юзера в платежной системе",
        null=True, blank=True,
        max_length=255
    )


class UserPerk(TimestampModel):
    perk = models.ForeignKey(
        "clubs.ClubPerk",
        related_name="used_users",
        on_delete=models.SET_NULL,
        null=True, blank=True
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="perks",
        null=True, blank=True
    )
