from django.contrib import admin
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)

from apps.authentication.models import TGAuthUser

admin.site.unregister(BlacklistedToken)
admin.site.unregister(OutstandingToken)
admin.site.register(TGAuthUser)