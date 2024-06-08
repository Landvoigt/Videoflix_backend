from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.contrib.auth.hashers import make_password

# not in use right now
class CustomUser(AbstractUser):
    custom = models.CharField(max_length=500, default="", blank=True)
    phone = models.CharField(max_length=20, default="", blank=True)
    address = models.CharField(max_length=200, default="", blank=True)

    groups = models.ManyToManyField(
        Group,
        related_name="customuser_set",
        blank=True,
        help_text="The groups this user belongs to.",
        verbose_name="groups",
        related_query_name="customuser",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="customuser_permissions_set",
        blank=True,
        help_text="Specific permissions for this user.",
        verbose_name="user permissions",
        related_query_name="customuser",
    )

    def save(self, *args, **kwargs):
        if not self.password.startswith("pbkdf2_sha256"):
            self.password = make_password(
                self.password
            )  # Hash the password same as in normal django user
        super().save(*args, **kwargs)
