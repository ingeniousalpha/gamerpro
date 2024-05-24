from uuid import uuid4

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _  # noqa
from django.contrib.contenttypes.fields import GenericRelation, GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from .managers import MainManager
from .utils import OverwriteStorage


class MainModel(models.Model):
    objects = MainManager()

    class Meta:
        abstract = True


class CharIDModel(MainModel):
    id = models.CharField(
        _("Уникальный код"),
        max_length=16,
        primary_key=True
    )

    class Meta:
        abstract = True


class UUIDModel(MainModel):
    uuid = models.UUIDField(
        "Идентификатор",
        default=uuid4,
        unique=True,
        editable=False,
        db_index=True
    )

    class Meta:
        abstract = True


class OuterIDModel(MainModel):
    outer_id = models.CharField("Внешний ID", max_length=256, null=True, blank=True)

    class Meta:
        abstract = True


class TimestampModel(MainModel):
    created_at = models.DateTimeField("Время создания", default=timezone.now, db_index=True)
    updated_at = models.DateTimeField("Время последнего изменения", auto_now=True, db_index=True)

    class Meta:
        abstract = True

    @property
    def created_at_pretty(self):
        return self.created_at.strftime("%d/%m/%Y %H:%M:%S")  # noqa

    @property
    def updated_at_pretty(self):
        return self.updated_at.strftime("%d/%m/%Y %H:%M:%S")  # noqa


class MultipleModelFK(MainModel):
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True)
    content_object = GenericForeignKey('content_type', 'object_id')


class HandledException(TimestampModel):
    code = models.TextField("Код ошибки", max_length=512)
    message = models.TextField("Описание ошибки", max_length=512)
    stack_trace = models.TextField("Traceback", null=True, blank=True)


class Document(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255)
    file = models.FileField(upload_to='documents', storage=OverwriteStorage())

    class Meta:
        verbose_name = "Документ"
        verbose_name_plural = "Документы"


class AppVersion(TimestampModel):
    number = models.IntegerField()
    platform = models.CharField(max_length=10, choices=[("IOS", "IOS"), ("ANDROID", "ANDROID")])
    app = models.CharField(max_length=10, choices=[("BRO", "BRO"), ("Lobby", "Lobby")])


class Country(models.Model):
    name = models.CharField(max_length=30)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Страна"
        verbose_name_plural = "* Страны"

    def __str__(self):
        return self.name


class City(models.Model):
    country = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        related_name="cities",
    )
    name = models.CharField(max_length=30)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Город"
        verbose_name_plural = "* Города"

    def __str__(self):
        return self.name
