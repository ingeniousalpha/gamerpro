from django.contrib import admin
from apps.clubs.admin import FilterByClubMixin
from .models import Booking


@admin.register(Booking)
class BookingAdmin(FilterByClubMixin, admin.ModelAdmin):
    search_fields = (
        'uuid', 'club_user__user__mobile_phone'
    )
    list_display = (
        'uuid', 'created_at', 'computers', 'amount', 'is_cancelled'
    )

    def computers(self, obj):
        return ", ".join([str(comp.computer.number) for comp in obj.computers.all()])
