from django.contrib import admin
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)

admin.site.unregister(BlacklistedToken)
admin.site.unregister(OutstandingToken)
