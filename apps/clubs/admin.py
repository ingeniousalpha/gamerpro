from django.contrib import admin
from django.http import HttpResponseRedirect
from .tasks import synchronize_gizmo_club_branch
from .models import *

admin.site.register(ClubComputerGroup)


@admin.register(ClubComputer)
class ClubComputerAdmin(admin.ModelAdmin):
    list_display = ('id', 'number', 'gizmo_hostname', 'is_booked')
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
    fields = ('id', 'group', 'gizmo_hostname', 'is_locked', 'is_active_session')


class ClubBranchTimePacketInline(admin.TabularInline):
    model = ClubTimePacket
    extra = 0
    readonly_fields = ('gizmo_name',)
    fields = ('gizmo_name', 'display_name', 'price', 'minutes')


class ClubBranchTimePacketGroupInline(admin.TabularInline):
    model = ClubTimePacketGroup
    extra = 0
    fields = ('name', 'is_active')
    show_change_link = True
    inlines = [ClubBranchTimePacketInline]


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
        'image',
    )
    inlines = [
        ClubComputerGroupInline,
        ClubBranchTimePacketGroupInline,
        ClubBranchPropertyInline,
        ClubBranchHardwareInline,
        ClubBranchPriceInline,
        ClubBranchComputerInline,
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
    search_fields = ('gizmo_id', 'login', 'gizmo_phone', 'user__mobile_phone')
    list_display = ('gizmo_id', 'login', 'club_branch')
    list_filter = ('club_branch',)


@admin.register(ClubTimePacketGroup)
class ClubTimePacketGroupAdmin(admin.ModelAdmin):
    list_display = ('gizmo_id', 'name', 'is_active')
    list_editable = ('is_active',)


@admin.register(ClubTimePacket)
class ClubTimePacketAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'gizmo_id',
        'display_name',
        'packet_group',
        'minutes',
        'price',
        'priority',
        'is_active',
    )
    list_filter = ('packet_group',)
    list_editable = ('priority', 'is_active')
    ordering = ['priority']


@admin.register(DayModel)
class DayModelAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'number',
    )
