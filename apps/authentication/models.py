import pyotp
from phonenumbers import PhoneNumber
from phonenumber_field.modelfields import PhoneNumberField
from django.db import models, transaction
from django.conf import settings

from apps.authentication.managers import OTPQueryset
from apps.common.models import TimestampModel


class OTP(TimestampModel):
    code = models.CharField("OTP", max_length=12, db_index=True, editable=False)
    verified = models.BooleanField("Подтверждён", default=False, editable=False)
    mobile_phone = PhoneNumberField("Мобильный телефон", editable=False)

    objects = OTPQueryset.as_manager()

    class Meta:
        verbose_name = "Одноразовый пароль"
        verbose_name_plural = "Одноразовые пароли"
        unique_together = ("code", "mobile_phone")

    @classmethod
    def generate(cls, mobile_phone: PhoneNumber):
        with transaction.atomic():
            instance = cls.objects.create()

            hotp = pyotp.HOTP(settings.HOTP_KEY, digits=settings.OTP_LENGTH)
            code = hotp.at(instance.pk)

            instance.code = code
            instance.mobile_phone = mobile_phone
            instance.save()
        return code


class TGAuthUser(models.Model):
    mobile_phone = models.CharField(max_length=12)
    chat_id = models.IntegerField(max_length=30)
    club_user = models.OneToOneField(
        "clubs.ClubBranchUser",
        on_delete=models.CASCADE,
        related_name="tg_user",
        null=True, blank=True
    )
