import uuid

from django.db import models
from django.contrib.auth.models import User


class EmailVerificationToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='verification_token')
    key = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Email verification token for {self.user}"
