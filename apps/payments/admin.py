from django.contrib import admin

from apps.payments.models import PaymentWebhook, Payment, PaymentCard


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
class PaymentAdmin(admin.ModelAdmin):
    search_fields = (
        'uuid',
        'outer_id'
    )
    inlines = [PaymentWebhookInline]


@admin.register(PaymentCard)
class PaymentCardAdmin(admin.ModelAdmin):
    search_fields = (
        'pay_token',
    )
