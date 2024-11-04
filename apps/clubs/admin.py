from django import forms
from django.forms import TextInput
from django_json_widget.widgets import JSONEditorWidget
from django.contrib import admin
from django.http import HttpResponseRedirect
from .tasks import synchronize_gizmo_club_branch
from .models import *
from apps.bot.tasks import bot_approve_user_from_admin_task, undelete_club_user_task, bot_create_gizmo_user_task
from ..payments.models import Payment


class ClubBranchListFilter(admin.SimpleListFilter):
    title = 'club branch'  # The title that will be displayed in the admin UI
    parameter_name = 'club_branch'  # The parameter used in the URL

    def lookups(self, request, model_admin):
        if not request.user.club_branches.exists():
            return []

        if model_admin.model == ClubPerk:
            self.parameter_name = "club"
        else:
            club_branches = request.user.club_branches.all()
            if club_branches.count() > 1:
                if model_admin.model == ClubTimePacket:
                    self.parameter_name = "club_computer_group__club_branch"
                elif model_admin.model == Payment:
                    self.parameter_name = "booking__club_branch"
                return [(branch.id, branch.name) for branch in club_branches]
        return []

    def queryset(self, request, queryset):
        # Filter the queryset based on the selected value
        if self.value():
            print("parameter_name: ", self.parameter_name)
            return queryset.filter(**{f"{self.parameter_name}_id": self.value()})
        return queryset


class FilterByClubMixin:
    club_filter_field = "club_branch"
    list_filter = (ClubBranchListFilter,)

    def get_queryset(self, request):
        print('FilterByClubMixin')
        queryset = super().get_queryset(request)

        if request.user.club_branches.exists():
            filter_data = {
                f"{self.club_filter_field}": request.user.club_branches.first().club
            } if self.club_filter_field == "club" else {
                f"{self.club_filter_field}__in": request.user.club_branches.all()
            }
            queryset = queryset.filter(**filter_data)

        return queryset


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
        # 'available_time_start',
        # 'available_time_end',
        'time_available',
        'is_active',
    )
    list_editable = ('priority', 'is_active', 'price',)
    ordering = ('priority',)
    club_filter_field = "packet_group__club_branch"

    def lookup_allowed(self, lookup, value):
        if lookup == 'club_computer_group__club_branch':
            return True
        return super().lookup_allowed(lookup, value)

    def days_available(self, obj):
        days = obj.available_days.values_list('name', flat=True)
        days_str = ", ".join(days)
        return days_str if days_str else '-'

    def time_available(self, obj):
        if obj.available_time_start and obj.available_time_end:
            return '{0}-{1}'.format(obj.available_time_start, obj.available_time_end)

        return '-'


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


@admin.register(ClubComputerLayoutGroup)
class ClubComputerLayoutGroupAdmin(FilterByClubMixin, admin.ModelAdmin):
    list_display = (
        'club_branch',
        'name',
        'outer_id',
        'is_available',
    )


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


class ClubComputerLayoutGroupInline(FilterByClubMixin, admin.TabularInline):
    model = ClubComputerLayoutGroup
    extra = 0
    fields = ('name', 'is_available')
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
        'id', 'group', 'layout_group', 'gizmo_id', 'gizmo_hostname',
        'is_locked', 'is_active_session', 'is_broken', 'is_deleted'
    )
    readonly_fields = ('group',)

    def get_queryset(self, request):
        qs = super(ClubBranchComputerInline, self).get_queryset(request)
        return qs.filter(is_deleted=False)


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


@admin.register(ClubPerk)
class ClubPerkAdmin(FilterByClubMixin, admin.ModelAdmin):
    club_filter_field = "club"
    list_display = ('club', 'code', 'name')


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
        ClubComputerLayoutGroupInline,
        ClubBranchTimePacketGroupInline,
        ClubBranchPropertyInline,
        ClubBranchHardwareInline,
        ClubBranchPriceInline,
        ClubBranchComputerInline,
    ]
    list_filter = ()
    club_filter_field = "id"
    list_editable = ('priority', 'is_active', 'is_ready',)
    list_display = (
        'id',
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


class ClubBranchUserForm(forms.ModelForm):
    class Meta:
        model = ClubBranchUser
        fields = ['first_name', 'login', 'gizmo_phone', ]
        widgets = {
            'gizmo_phone': TextInput(attrs={'class': 'phone-mask', 'placeholder': '+7XXXZZZZZZZ'})
        }

    def __init__(self, *args, **kwargs):
        print("form args: ", args)
        print("form kwargs: ", kwargs)
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    def clean_login(self):

        login = self.cleaned_data.get('login')
        if "bot_approve_user_from_admin" in self.request.POST or "undelete_club_user" in self.request.POST:
            return login

        # Check if a user with this login already exists
        if ClubBranchUser.objects.filter(
                club_branch__in=self.request.user.club_branches.all(), login=login
        ).exists():
            raise forms.ValidationError("Игрок с таким ИИН уже существует. Найдите его в поисковике")

        return login

    def save(self, commit=True):
        instance = super().save(commit=False)

        if not instance.club_branch:
            instance.club_branch = (self.request.user.club_branches.first() or
                           ClubBranch.objects.filter(is_bro_chain=True).first())
            instance.created_by = self.request.user

        instance.save()

        bot_create_gizmo_user_task(self.cleaned_data["login"], instance.club_branch.id)
        instance.refresh_from_db()
        return instance


@admin.register(ClubBranchUser)
class ClubBranchUserAdmin(FilterByClubMixin, admin.ModelAdmin):
    search_fields = ('gizmo_id', 'login', 'gizmo_phone', 'user__mobile_phone', 'first_name')
    list_display = ('gizmo_id', 'login', 'gizmo_phone', 'club_branch', 'created_at',)
    form = ClubBranchUserForm

    def get_form(self, request, obj=None, **kwargs):
        # Get the default form
        Form = super().get_form(request, obj, **kwargs)

        # Create a new form class that includes the request
        class FormWithRequest(Form):
            def __init__(self, *args, **kws):
                kws['request'] = request
                super().__init__(*args, **kws)

        # Return the new form class
        return FormWithRequest

    def get_fields(self, request, obj=None):
        # Check if we are adding a new object or changing an existing one
        if obj is None:  # This means we are in the "Add" view
            return ('first_name', 'login', 'gizmo_phone')
        else:  # This means we are in the "Change" view
            return (
                'created_at',
                'club_branch',
                'user',
                'gizmo_id',
                'gizmo_phone',
                'login',
                'first_name',
                'created_by',
            )

    # def response_change(self, request, obj):
    #     if "bot_approve_user_from_admin" in request.POST:
    #         print('bot_approve_user_from_admin')
    #         bot_approve_user_from_admin_task(obj.id)
    #         self.message_user(request, "Верифицируем и создаем аккаунт юзера...")
    #         return HttpResponseRedirect(".")
    #     elif "undelete_club_user" in request.POST:
    #         undelete_club_user_task.delay(obj.id)
    #         self.message_user(request, "Отменяем удаление юзеру в Гизме")
    #         return HttpResponseRedirect(".")
    #     return super().response_change(request, obj)


class ClubBranchUserInline(admin.TabularInline):
    model = ClubBranchUser
    fk_name = 'user'
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


@admin.register(DayModel)
class DayModelAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'number',
    )


@admin.register(ClubBranchAdmin)
class ClubBranchAdminModelAdmin(FilterByClubMixin, admin.ModelAdmin):
    list_display = (
        'mobile_phone',
        'tg_chat_id',
        'tg_username',
        'is_active',
        'club_branch',
    )


@admin.register(ClubComputerGroup)
class ClubComputerGroupAdmin(FilterByClubMixin, admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'gizmo_id',
        'is_deleted',
        'club_branch',
    )


@admin.register(ClubBranchLegalEntity)
class ClubBranchLegalEntityAdmin(admin.ModelAdmin):
    list_display = (
        'id',
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
