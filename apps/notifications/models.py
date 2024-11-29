from django.contrib.auth import get_user_model
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from apps.common.models import TimestampModel

User = get_user_model()


class FirebaseToken(TimestampModel):
    token = models.TextField()
    device_id = models.CharField(
        max_length=255,
        null=True, blank=True
    )
    user = models.ForeignKey(
        User,
        related_name="fb_tokens",
        on_delete=models.CASCADE,
        null=True, blank=True
    )


class JaryqLabOrder(TimestampModel):
    name = models.CharField(max_length=50, verbose_name="Имя")
    email = models.EmailField(max_length=50, verbose_name="Почта")
    phone_number = models.CharField(max_length=20, verbose_name="Номер телефона")
    description = models.TextField(verbose_name="Описание")

    def __str__(self):
        return f"Заказ {self.id}"
