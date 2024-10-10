from django.contrib import admin
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)

from apps.authentication.models import TGAuthUser, VerifiedOTP

admin.site.unregister(BlacklistedToken)
admin.site.unregister(OutstandingToken)


@admin.register(TGAuthUser)
class TGAuthUserAdmin(admin.ModelAdmin):
    list_display = (
        'mobile_phone',
        'chat_id',
    )
    search_fields = (
        'mobile_phone',
        'chat_id',
    )


@admin.register(VerifiedOTP)
class VerifiedOTPAdmin(admin.ModelAdmin):
    list_display = (
        'mobile_phone',
        'otp_code',
        'user',
        'created_at',
    )
    search_fields = (
        'mobile_phone',
    )


class VerifiedOTPInline(admin.TabularInline):
    model = VerifiedOTP
    extra = 0
    fields = (
        'mobile_phone',
        'otp_code',
        'created_at',
    )
    readonly_fields = (
        'mobile_phone',
        'otp_code',
        'created_at',
    )

    def get_queryset(self, request):
        return super().get_queryset(request).order_by('-created_at')
