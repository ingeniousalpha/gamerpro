from django.contrib import admin
from django.http import HttpResponseRedirect
from .tasks import synchronize_gizmo_club_branch
from .models import *

admin.site.register(ClubComputerGroup)


@admin.register(ClubComputer)
class ClubComputerAdmin(admin.ModelAdmin):
    list_display = ('number', 'gizmo_hostname',)
    ordering = ('number',)


class ClubBranchInline(admin.StackedInline):
    model = ClubBranch
    extra = 0
    fields = ('name',)


class ClubComputerGroupInline(admin.TabularInline):
    model = ClubComputerGroup
    extra = 0
    fields = ('name',)
    readonly_fields = ('name',)
    can_delete = False


class ClubBranchPropertyInline(admin.TabularInline):
    model = ClubBranchProperty
    extra = 0
    fields = ('group', 'name')


class ClubBranchHardwareInline(admin.TabularInline):
    model = ClubBranchHardware
    extra = 0
    fields = ('group', 'name')


class ClubBranchPriceInline(admin.TabularInline):
    model = ClubBranchPrice
    extra = 0
    fields = ('group', 'name', 'price')


class ClubBranchComputerInline(admin.TabularInline):
    model = ClubComputer
    extra = 0
    ordering = ['number']
    fields = ('group', 'gizmo_hostname', 'is_booked')


@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    fields = ('name', 'description')
    inlines = [ClubBranchInline]


@admin.register(ClubBranch)
class ClubBranchAdmin(admin.ModelAdmin):
    fields = (
        'name',
        'address',
        'club',
        'api_host',
        'api_user',
        'api_password',
        'gizmo_payment_method',
        'is_active',
    )
    inlines = [
        ClubComputerGroupInline,
        ClubBranchPropertyInline,
        ClubBranchHardwareInline,
        ClubBranchPriceInline,
        ClubBranchComputerInline
    ]

    def response_change(self, request, obj):
        if "sync_gizmo" in request.POST:
            print('sync_gizmo')
            synchronize_gizmo_club_branch.delay(obj.id)
            self.message_user(request, "Synchronizing GIZMO club info")
            return HttpResponseRedirect(".")
        return super().response_change(request, obj)


@admin.register(ClubBranchUser)
class ClubBranchUserAdmin(admin.ModelAdmin):
    search_fields = ('gizmo_id', 'login',)
    list_display = ('gizmo_id', 'login', 'club_branch')
    list_filter = ('club_branch',)