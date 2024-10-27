from django.contrib import admin

from apps.payments.models import PaymentWebhook, Payment, PaymentCard
from apps.clubs.admin import FilterByClubMixin


@admin.register(PaymentWebhook)
class PaymentWebhookAdmin(admin.ModelAdmin):
    search_fields = (
        'transaction_id',
        'booking_uuid',
    )
    list_display = (
        'transaction_id',
        'booking_uuid',
        'payment'
    )


class PaymentWebhookInline(admin.StackedInline):
    model = PaymentWebhook
    fields = ('data',)
    extra = 0


@admin.register(Payment)
class PaymentAdmin(FilterByClubMixin, admin.ModelAdmin):
    search_fields = (
        'uuid',
        'outer_id'
    )
    list_display = (
        'uuid',
        'created_at',
        'status',
        'amount',
        'provider',
        'card',
        'booking',
        'user',
    )
    list_filter = (
        'created_at',
        'status',
        'provider',
        # 'user',
    )
    date_hierarchy = 'created_at'
    inlines = [PaymentWebhookInline]
    club_filter_field = "booking__club_branch__club"


@admin.register(PaymentCard)
class PaymentCardAdmin(admin.ModelAdmin):
    search_fields = (
        'pay_token',
    )
