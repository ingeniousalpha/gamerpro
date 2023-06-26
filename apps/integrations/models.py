from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils.translation import gettext_lazy as _

from apps.common.models import TimestampModel

from . import ServiceStatuses


class ServiceHistory(TimestampModel):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField(null=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    service = models.CharField(_("Класс"), max_length=255)
    service_pretty = models.CharField(_("Сервис"), max_length=255)
    data = models.JSONField(_("Данные"), null=True, blank=True)
    status = models.CharField(
        _("Статус"),
        choices=ServiceStatuses.choices,
        max_length=255,
        default=ServiceStatuses.NO_REQUEST
    )
    created_at = models.DateTimeField(_("Дата запроса"), auto_now_add=True, null=True, db_index=True)
    runtime = models.DecimalField(_("Выполнено за(сек)"), max_digits=6, decimal_places=3, default=0.0)


    class Meta:
        verbose_name = _("История запросов")
        verbose_name_plural = _("Сервисы: История запросов")
        ordering = ("-id",)

    @property
    def response(self):
        if hasattr(self, "service_response"):
            return self.service_response
        return None

    def set_response(self, **kwargs):
        return ServiceResponse.objects.create(
            history=self,
            **kwargs
        )

    def __str__(self):
        return f"{self.service_pretty} - {self.content_object}"


class ServiceResponse(models.Model):
    history = models.OneToOneField(
        ServiceHistory,
        on_delete=models.CASCADE,
        related_name="service_response",
        verbose_name=_("Лог")
    )
    url = models.CharField(_("Ссылка"), max_length=255, null=True, blank=True)
    method = models.CharField(_("Метод"), max_length=100, null=True, blank=True)
    request = models.TextField(_("Параметры запроса"), null=True, blank=True)
    response = models.TextField(_("Ответ от сервиса"), null=True, blank=True)
    code = models.CharField(_("Код ответа"), max_length=5, null=True, blank=True)
    created_at = models.DateTimeField(
        _("Дата запроса"), auto_now_add=True, db_index=True
    )

    class Meta:
        verbose_name = _("Лог сервиса")
        verbose_name_plural = _("Логи от сервисов")

    def __str__(self):
        return self.history.service.__str__()
