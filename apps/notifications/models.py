from django.contrib.auth import get_user_model
from django.db import models

from apps.common.models import TimestampModel

User = get_user_model()


class FirebaseToken(TimestampModel):
    token = models.TextField()
    user = models.ForeignKey(
        User,
        related_name="fb_tokens",
        on_delete=models.CASCADE,
        null=True, blank=True
    )
