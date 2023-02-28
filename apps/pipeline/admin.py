from django.contrib import admin
from django.db.models import Model
from django.http import HttpResponse
from django.urls import reverse, path
from django.utils import timezone, dateformat
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from apps.common.admin import ReadOnlyMixin

from .models import ServiceHistory, ServiceResponse


class ServiceResponseInline(ReadOnlyMixin, admin.StackedInline):
    model = ServiceResponse
    extra = 0
    fields = [
        'url',
        'method',
        'code',
        'get_request',
        'get_response',
    ]
    readonly_fields = [
        'get_request',
        'get_response',
    ]

    def get_request(self, obj: ServiceResponse):
        if obj is None or obj.request is None:
            return 'no content'

        if len(obj.request) > 4096:
            return format_html(
                '<a href="{}">Скачать запрос</a>',
                reverse('admin:pipeline_servicehistory_request_log', args=[obj.id, 'request'])
            )

        return obj.request or '-'

    def get_response(self, obj: ServiceResponse):
        if obj is None or obj.response is None:
            return 'no content'

        if len(obj.response) > 4096:
            return format_html(
                '<a href="{}">Скачать ответ</a>',
                reverse('admin:pipeline_servicehistory_request_log', args=[obj.id, 'response'])
            )

        return obj.response or '-'


class ServiceHistoryAdmin(admin.ModelAdmin):
    list_display = ("id", "link_content_object", "service", "service_pretty", "status", "created_at", "runtime")
    list_filter = ("service", "status")

    readonly_fields = ("link_content_object", "service", "status", "data", "runtime")
    inlines = [ServiceResponseInline]
    date_hierarchy = "created_at"

    fieldsets = (
        (None, {
            "fields": (
                "link_content_object",
                "service",
                ("status", "runtime"),
                "data",
            )
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('content_object')

    def link_content_object(self, instance: ServiceHistory):
        obj: Model = instance.content_object
        if not obj:
            return "-"

        change_url = reverse(
            'admin:%s_%s_change' % (
                obj._meta.app_label,
                obj._meta.object_name.lower()
            ),
            args=(obj.id,)
        )
        return mark_safe(f"<a href='{change_url}'>{f'{obj._meta.verbose_name.capitalize()}: {obj.id}'}</a>")

    link_content_object.allow_tags = True   # noqa
    link_content_object.short_description = _('in relation to') # noqa

    def get_urls(self):
        url_name = '%s_%s_request_log' % (self.model._meta.app_label, self.model._meta.model_name)
        urls = [path('service-log/<int:pk>/<str:direct>/download', self.service_log, name=url_name),]
        return super().get_urls() + urls

    # add custom view function that downloads the file
    def service_log(self, request, pk: int, direct: str = 'request'):
        timestamp = dateformat.format(timezone.now(), 'Y-m-d-H-i-s')
        log = ServiceResponse.objects.get(pk=pk)
        response = HttpResponse(content_type='applications/force-download')
        response['Content-Disposition'] = f'attachment; filename="request-log-{timestamp}.txt"'
        response.write(getattr(log, direct, ''))
        return response


admin.site.register(ServiceHistory, ServiceHistoryAdmin)
