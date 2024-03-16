from django.contrib import admin
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)

from apps.authentication.models import TGAuthUser

admin.site.unregister(BlacklistedToken)
admin.site.unregister(OutstandingToken)


@admin.register(TGAuthUser)
class TGAuthUserAdmin(admin.ModelAdmin):
    fields = (
        'mobile_phone',
        'chat_id',
    )
    search_fields = (
        'mobile_phone',
        'chat_id',
    )
