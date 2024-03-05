from django.contrib import admin
from django.http import HttpResponseRedirect
from .tasks import synchronize_gizmo_club_branch
from .models import *

admin.site.register(ClubComputerGroup)


class FilterByClubMixin:
    club_filter_field = "club_branch__club"
    list_filter = ('club_branch',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)

        filter_data = {
            self.club_filter_field: request.user.club
        }

        if request.user.club:
            queryset = queryset.filter(**filter_data)
        return queryset


@admin.register(ClubComputer)
class ClubComputerAdmin(FilterByClubMixin, admin.ModelAdmin):
    list_display = ('id', 'number', 'gizmo_hostname', 'is_booked')
    ordering = ('number',)


class ClubBranchInline(FilterByClubMixin, admin.StackedInline):
    model = ClubBranch
    extra = 0
    fields = ('name',)


class ClubComputerGroupInline(FilterByClubMixin, admin.TabularInline):
    model = ClubComputerGroup
    extra = 0
    fields = ('name',)
    readonly_fields = ('name',)
    can_delete = False


class ClubBranchPropertyInline(FilterByClubMixin, admin.TabularInline):
    model = ClubBranchProperty
    extra = 0
    fields = ('group', 'name')


class ClubBranchHardwareInline(FilterByClubMixin, admin.TabularInline):
    model = ClubBranchHardware
    extra = 0
    fields = ('group', 'name')


class ClubBranchPriceInline(FilterByClubMixin, admin.TabularInline):
    model = ClubBranchPrice
    extra = 0
    fields = ('group', 'name', 'price')


class ClubBranchComputerInline(FilterByClubMixin, admin.TabularInline):
    model = ClubComputer
    extra = 0
    ordering = ['number']
    fields = ('id', 'group', 'gizmo_hostname', 'is_locked', 'is_active_session')


class ClubBranchTimePacketInline(FilterByClubMixin, admin.TabularInline):
    model = ClubTimePacket
    extra = 0
    readonly_fields = ('gizmo_name',)
    fields = ('gizmo_name', 'display_name', 'price', 'minutes')


class ClubBranchTimePacketGroupInline(FilterByClubMixin, admin.TabularInline):
    model = ClubTimePacketGroup
    extra = 0
    fields = ('name', 'is_active')
    show_change_link = True
    inlines = [ClubBranchTimePacketInline]


@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    inlines = [ClubBranchInline]
    fields = (
        'name',
        'description',
        'code',
        'is_bro_chain',
    )


@admin.register(ClubBranch)
class ClubBranchModelAdmin(FilterByClubMixin, admin.ModelAdmin):
    fields = (
        'name',
        'trader_name',
        'trader',
        'address',
        'club',
        'api_host',
        'api_user',
        'api_password',
        'gizmo_payment_method',
        'is_active',
        'is_ready',
        'priority',
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
    club_filter_field = "club"
    list_filter = ('club',)
    list_editable = ('priority', 'is_active', 'is_ready',)
    list_display = ('__str__', 'priority', 'is_active', 'is_ready',)

    def response_change(self, request, obj):
        if "sync_gizmo" in request.POST:
            print('sync_gizmo')
            synchronize_gizmo_club_branch.delay(obj.id)
            self.message_user(request, "Synchronizing GIZMO club info")
            return HttpResponseRedirect(".")
        return super().response_change(request, obj)


@admin.register(ClubBranchUser)
class ClubBranchUserAdmin(FilterByClubMixin, admin.ModelAdmin):
    search_fields = ('gizmo_id', 'login', 'gizmo_phone', 'user__mobile_phone', 'first_name')
    list_display = ('gizmo_id', 'login', 'gizmo_phone', 'club_branch')


class ClubBranchUserInline(admin.TabularInline):
    model = ClubBranchUser
    extra = 0
    fields = (
        "club_branch",
        "gizmo_id",
        "gizmo_phone",
        "login",
        "first_name",
        "balance",
    )


@admin.register(ClubTimePacketGroup)
class ClubTimePacketGroupAdmin(FilterByClubMixin, admin.ModelAdmin):
    list_display = ('gizmo_id', 'name', 'is_active', 'club_branch')
    list_editable = ('is_active',)


@admin.register(ClubTimePacket)
class ClubTimePacketAdmin(FilterByClubMixin, admin.ModelAdmin):
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
    list_filter = ('packet_group', 'club_computer_group__club_branch',)
    list_editable = ('priority', 'is_active')
    ordering = ['priority']
    club_filter_field = "packet_group__club_branch__club"


@admin.register(DayModel)
class DayModelAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'number',
    )


@admin.register(ClubBranchAdmin)
class ClubBranchAdminModelAdmin(admin.ModelAdmin):
    list_display = (
        'mobile_phone',
        'tg_chat_id',
        'tg_username',
        'is_active',
        'club_branch',
    )
    list_filter = (
        'club_branch',
    )


@admin.register(ClubBranchLegalEntity)
class ClubBranchLegalEntityAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'code',
    )
    search_fields = (
        'code',
        'name',
    )
