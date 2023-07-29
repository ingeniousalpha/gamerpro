from django.contrib import admin

from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    search_fields = (
        'uuid',
    )
    list_display = (
        'uuid', 'created_at', 'computers', 'amount', 'is_cancelled'
    )

    def computers(self, obj):
        return ", ".join([str(comp.computer.number) for comp in obj.computers.all()])
