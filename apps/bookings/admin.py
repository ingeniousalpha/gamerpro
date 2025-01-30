from django.contrib import admin
from django.http import HttpResponseRedirect
from django.utils.safestring import mark_safe
from apps.clubs.admin import FilterByClubMixin
from .models import Booking, BookedComputer
from .tasks import gizmo_bro_add_time_and_set_booking_expiration
from ..payments import PaymentStatuses, PaymentProviders
from ..payments.models import Payment


class BookedComputerInline(admin.TabularInline):
    model = BookedComputer
    fields = ('computer', 'is_active_session', 'is_locked',)
    readonly_fields = ('is_active_session', 'is_locked',)
    extra = 0
    can_delete = False


class BookingPaymentInline(admin.TabularInline):
    model = Payment
    fields = (
        'outer_id',
        'status',
        'status_reason',
        'amount',
        'provider',
        'card',
        'replenishment',
    )
    extra = 0
    can_delete = False


@admin.register(Booking)
class BookingAdmin(FilterByClubMixin, admin.ModelAdmin):
    search_fields = (
        'uuid', 'club_user__user__mobile_phone', 'club_user__login',
    )
    list_display = (
        'uuid', 'club_user', 'club_branch', 'computers', 'amount', 'is_cancelled', 'is_paid', 'created_at'
    )
    readonly_fields = (
        'uuid',
        'expiration_date',
        'club_branch',
        'club_user',
        'payment_card',
        'is_time_packet_set',
    )

    def get_fields(self, request, obj=None):
        fields = [
            'uuid',
            'created_at',
            'club_branch',
            'club_user',
            'status',
            'use_balance',
            'use_cashback',
            'for_free',
            'platform',
            'amount',
            'commission_amount',
            'total_amount',
            'payment_card',
            'expiration_date',
            'is_starting_session',
            'time_packet',
        ]
        if request.user.is_superuser:
            fields.append('is_cancelled')
            fields.append('is_time_packet_set')
        return fields

    def response_change(self, request, obj):
        if True  or "set_time_packet" in request.POST:
            if obj.is_time_packet_set:
                self.message_user(request, "Task gizmo_bro_add_time_and_set_booking_expiration уже запускался")
            else:
                gizmo_bro_add_time_and_set_booking_expiration.delay(str(obj.uuid))
                self.message_user(request, "Task gizmo_bro_add_time_and_set_booking_expiration запущен")
            return HttpResponseRedirect(".")
        return super().response_change(request, obj)

    def computers(self, obj):
        return ", ".join([str(comp.computer.number) for comp in obj.computers.all()])

    def is_paid(self, obj):
         if obj.payments.exists() and obj.payments.filter(status=PaymentStatuses.PAYMENT_APPROVED).exists():
             if obj.payments.filter(status=PaymentStatuses.PAYMENT_APPROVED).first().provider == PaymentProviders.KASPI:
                 return mark_safe(f'<div style="background:#52C135;">Оплачено KASPI</div>')
             return mark_safe(f'<div style="background:#52C135;">Оплачено</div>')
         if obj.use_cashback:
             return mark_safe(f'<div style="background:#52C135;">Оплачено Бонусами</div>')
         if obj.for_free:
             return mark_safe(f'<div style="background:#52C135;">Бесплатно</div>')
         return "Не оплачено"
    is_paid.short_description = "Статус оплаты"

    inlines = [
        BookedComputerInline,
        BookingPaymentInline
    ]
