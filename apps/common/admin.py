# from ckeditor_uploader.fields import RichTextUploadingField
# from ckeditor_uploader.widgets import CKEditorUploadingWidget
from django import forms
from django.urls import reverse
from django.contrib import admin
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.admin import GenericTabularInline, GenericStackedInline

from apps.clubs.admin import ClubBranchInline
from apps.common.models import HandledException, Document, AppVersion, City, Country

admin.site.site_header = "Gamer Pro Project"
admin.site.site_title = "Gamer Pro Project"
admin.site.index_title = ""


class HiddenAdmin(admin.ModelAdmin):
    def get_model_perms(self, request):
        return {}  # Hide model in admin list


class ChangeOnlyMixin:
    def has_add_permission(self, request, obj=None):
        return False


class ReadOnlyMixin(ChangeOnlyMixin):
    def has_change_permission(self, request, obj=None):
        return False


class ReadChangeOnlyMixin():
    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj):
        return False


class ReadChangeOnlyTabularInline(ReadChangeOnlyMixin, admin.TabularInline):
    ...


class ReadChangeOnlyStackedInline(ReadChangeOnlyTabularInline, admin.StackedInline):
    ...


@admin.register(HandledException)
class HandledExceptionAdmin(admin.ModelAdmin):
    fields = (
        'id',
        'created_at',
        'code',
        'message',
        'stack_trace',
    )
    list_display = ('id', 'code', 'message', 'created_at')
    search_fields = ('id', 'code')
    readonly_fields = ('created_at', 'id')
    date_hierarchy = 'created_at'


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    fields = (
        'name',
        'code',
        'file'
    )
    list_display = (
        'id',
        'name',
        'code'
    )


@admin.register(AppVersion)
class AppVersionAdmin(admin.ModelAdmin):
    list_display = (
        'number', 'app', 'platform', 'updated_at',
    )
    list_filter = (
        'app',
        'platform',
    )
    fields = (
        'updated_at', 'app', 'platform', 'number',
    )
    readonly_fields = ('updated_at',)


class CityInline(admin.StackedInline):
    model = City
    fields = ('name', 'is_active')
    extra = 0


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_editable = ('is_active',)

    inlines = [ClubBranchInline]


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_editable = ('is_active',)

    inlines = [CityInline]
