from django_json_widget.widgets import JSONEditorWidget
from django.contrib import admin
from django.http import HttpResponseRedirect
from .tasks import synchronize_gizmo_club_branch
from .models import *
from apps.bot.tasks import bot_approve_user_from_admin_task
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
    ordering = ('number',)
    list_display = (
        'id',
        'group',
        'gizmo_id',
        'number',
        'gizmo_hostname',
        'is_booked',
        'is_active_session',
        'is_locked',
        'is_broken',
        'is_deleted',
    )
    list_filter = FilterByClubMixin.list_filter + ('is_deleted',)


class ClubBranchInline(FilterByClubMixin, admin.TabularInline):
    model = ClubBranch
    extra = 0
    fields = ('name', 'api_host',)
    readonly_fields = ('name', 'api_host')
    show_change_link = ('name',)


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
    fields = (
        'id', 'group', 'gizmo_id', 'gizmo_hostname',
        'is_locked', 'is_active_session', 'is_broken', 'is_deleted'
    )
    readonly_fields = ('group',)


class ClubBranchTimePacketInline(FilterByClubMixin, admin.TabularInline):
    model = ClubTimePacket
    extra = 0
    readonly_fields = ('gizmo_name',)
    fields = ('gizmo_name', 'display_name', 'price', 'minutes')


class ClubBranchTimePacketGroupInline(FilterByClubMixin, admin.TabularInline):
    model = ClubTimePacketGroup
    extra = 0
    fields = ('name', 'is_active', 'computer_group')
    readonly_fields = ('name', 'computer_group',)
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
        'club',
        'name',
        'trader_name',
        'trader',
        'address',
        'city',
        'api_host',
        'api_user',
        'api_password',
        'gizmo_payment_method',
        'gizmo_points_method',
        'is_active',
        'is_ready',
        'is_turned_on',
        'priority',
        'image',
        'extra_data',
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
    list_display = (
        '__str__',
        'api_host',
        'priority',
        'is_active',
        'is_ready',

    )
    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget},
    }

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

    def response_change(self, request, obj):
        if "bot_approve_user_from_admin" in request.POST:
            print('bot_approve_user_from_admin')
            bot_approve_user_from_admin_task.delay(obj.id)
            self.message_user(request, "Верифицируем и создаем аккаунт юзера...")
            return HttpResponseRedirect(".")
        return super().response_change(request, obj)


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


class ClubUserCashbackInline(admin.TabularInline):
    model = ClubUserCashback
    extra = 0
    fields = (
        'club',
        'cashback_amount',
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
        'club_computer_group',
        'minutes',
        'price',
        'priority',
        'days_available',
        #'available_time_start',
        #'available_time_end',
        'time_available',
        'is_active',
    )
    list_filter = ('club_computer_group__club_branch',)
    list_editable = ('priority', 'is_active', 'price',)
    ordering = ('priority',)
    club_filter_field = "packet_group__club_branch__club"

    def days_available(self, obj):
        days = obj.available_days.values_list('name', flat=True)
        days_str = ", ".join(days)
        return days_str if days_str else '-'
    
    
    def time_available(self, obj):
        if obj.available_time_start and obj.available_time_end:
            return '{0}-{1}'.format(obj.available_time_start, obj.available_time_end)
        
        return '-'


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
        'branches_amount',
    )
    search_fields = (
        'code',
        'name',
    )
    readonly_fields = ('branches_amount',)
    inlines = [
        ClubBranchInline,
    ]

    def branches_amount(self, obj):
        return obj.club_branches.count()
