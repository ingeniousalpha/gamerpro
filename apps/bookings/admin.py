from django.contrib import admin
from apps.clubs.admin import FilterByClubMixin
from .models import Booking, BookedComputer


class BookedComputerInline(admin.TabularInline):
    model = BookedComputer
    fields = ('computer', 'is_active_session', 'is_locked',)
    readonly_fields = ('is_active_session', 'is_locked',)
    extra = 0
    can_delete = False


@admin.register(Booking)
class BookingAdmin(FilterByClubMixin, admin.ModelAdmin):
    search_fields = (
        'uuid', 'club_user__user__mobile_phone', 'club_user__login',
    )
    list_display = (
        'uuid', 'club_user', 'created_at', 'computers', 'amount', 'is_cancelled'
    )
    readonly_fields = (
        'club_branch',
        'club_user',
        'payment_card',
    )

    def computers(self, obj):
        return ", ".join([str(comp.computer.number) for comp in obj.computers.all()])

    inlines = [BookedComputerInline]
